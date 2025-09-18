from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Q
from django.http import HttpResponse
import csv
from datetime import datetime
from api.models import UserProfile, FormTemplate, FormField, Employee, EmployeeFieldValue, AuditLog
import json


def home(request):
    """Home page - redirect to login or dashboard"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'dashboard/login.html')


@login_required
def dashboard(request):
    """Main dashboard view"""
    return render(request, 'dashboard/dashboard.html')


def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'dashboard/login.html')


@login_required
def form_builder(request):
    """Form builder page"""
    if request.method == 'POST':
        name = request.POST.get('form_name')
        description = request.POST.get('form_description')
        fields_json = request.POST.get('fields_json')

        if not name:
            messages.error(request, 'Form name is required')
            return redirect('form_builder')

        try:
            fields_data = json.loads(fields_json or '[]')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid fields data')
            return redirect('form_builder')

        form_template = FormTemplate.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )

        for index, field in enumerate(fields_data):
            FormField.objects.create(
                form_template=form_template,
                field_name=field.get('field_name') or f"field_{index}",
                field_type=field.get('field_type') or 'text',
                field_label=field.get('field_label') or f"Field {index+1}",
                is_required=bool(field.get('is_required')),
                placeholder=field.get('placeholder') or '',
                help_text=field.get('help_text') or '',
                order=field.get('order') or index,
                options=field.get('options') or None,
            )

        messages.success(request, 'Form template created successfully')
        return redirect('form_builder')

    # Preload existing templates for initial render if needed
    templates = FormTemplate.objects.order_by('-created_at')[:20]
    return render(request, 'dashboard/form_builder.html', { 'templates': templates })


@login_required
def employee_management(request):
    """Employee management page"""
    q = request.GET.get('search')
    form_template_id = request.GET.get('form_template')
    is_active = request.GET.get('is_active')

    employees = Employee.objects.all().select_related('form_template').prefetch_related('field_values')
    if q:
        employees = employees.filter(
            Q(field_values__value__icontains=q) |
            Q(employee_id__icontains=q)
        ).distinct()
    if form_template_id:
        employees = employees.filter(form_template_id=form_template_id)
    if is_active in ['true', 'false']:
        employees = employees.filter(is_active=(is_active == 'true'))

    employees = employees.order_by('-created_at')[:50]
    form_templates = FormTemplate.objects.order_by('name')
    return render(request, 'dashboard/employee_management.html', {
        'employees': employees,
        'form_templates': form_templates,
        'filters': {
            'search': q or '',
            'form_template': form_template_id or '',
            'is_active': is_active or ''
        }
    })


@login_required
def employee_export(request):
    """Export employees as CSV (Excel-compatible), honoring current filters"""
    q = request.GET.get('search')
    form_template_id = request.GET.get('form_template')
    is_active = request.GET.get('is_active')

    employees = Employee.objects.all().select_related('form_template').prefetch_related('field_values__field')
    if q:
        employees = employees.filter(
            Q(field_values__value__icontains=q) |
            Q(employee_id__icontains=q)
        ).distinct()
    if form_template_id:
        employees = employees.filter(form_template_id=form_template_id)
    if is_active in ['true', 'false']:
        employees = employees.filter(is_active=(is_active == 'true'))

    response = HttpResponse(content_type='text/csv')
    filename = f"employees_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Employee UUID', 'Name', 'Form Template', 'Created At', 'Active', 'Field Values (JSON)'])

    for e in employees.order_by('-created_at'):
        # Build a simple dict of field label to value
        field_map = {}
        for fv in e.field_values.all():
            display_value = fv.value if fv.value else (fv.file_value.url if getattr(fv.file_value, 'url', None) else '')
            field_map[fv.field.field_label] = display_value
        writer.writerow([
            str(e.employee_id),
            e.employee_name,
            e.form_template.name,
            e.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes' if e.is_active else 'No',
            json.dumps(field_map, ensure_ascii=False)
        ])

    return response


@login_required
def profile(request):
    """User profile page"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        profile_picture = request.FILES.get('profile_picture')

        # Ensure profile exists
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

        user_profile.phone_number = phone_number
        user_profile.address = address
        if isinstance(profile_picture, UploadedFile):
            user_profile.profile_picture = profile_picture
        user_profile.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('profile')

    return render(request, 'dashboard/profile.html')


@login_required
def change_password(request):
    """Change password page"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password or ''):
            messages.error(request, 'Current password is incorrect')
            return redirect('change_password')

        if not new_password:
            messages.error(request, 'New password cannot be empty')
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, 'New password and confirmation do not match')
            return redirect('change_password')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Password changed successfully')
        return redirect('change_password')

    return render(request, 'dashboard/change_password.html')


@login_required
def employee_create(request):
    """Employee creation page"""
    if request.method == 'POST':
        form_template_id = request.POST.get('form_template')
        field_values_json = request.POST.get('field_values_json')

        if not form_template_id:
            messages.error(request, 'Please select a form template')
            form_templates = FormTemplate.objects.order_by('name')
            return render(request, 'dashboard/employee_create.html', {
                'form_templates': form_templates,
                'selected_form_template': '',
            })

        try:
            field_values_data = json.loads(field_values_json or '{}')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid field values. Please try again.')
            form_templates = FormTemplate.objects.order_by('name')
            return render(request, 'dashboard/employee_create.html', {
                'form_templates': form_templates,
                'selected_form_template': form_template_id,
            })

        # Validate required fields
        validation_errors = []
        fields = FormField.objects.filter(form_template_id=form_template_id)
        for field in fields:
            if field.is_required:
                if field.field_type == 'file':
                    # Check if file was uploaded
                    uploaded_file = request.FILES.get(f'field_{field.id}')
                    if not uploaded_file:
                        validation_errors.append(f"{field.field_label} is required")
                else:
                    # Check regular form fields
                    raw_value = field_values_data.get(str(field.id))
                    if raw_value in [None, '', False]:
                        validation_errors.append(f"{field.field_label} is required")

        if not field_values_data:
            validation_errors.append('No field data was submitted. Please fill the form fields and try again.')

        if validation_errors:
            for err in validation_errors:
                messages.error(request, err)
            # Build server-rendered fields with submitted values and error hints
            form_templates = FormTemplate.objects.order_by('name')
            field_defs = []
            for f in fields.order_by('order', 'id'):
                submitted = field_values_data.get(str(f.id), '')
                field_defs.append({
                    'id': f.id,
                    'field_label': f.field_label,
                    'field_name': f.field_name,
                    'field_type': f.field_type,
                    'is_required': f.is_required,
                    'placeholder': f.placeholder or '',
                    'help_text': f.help_text or '',
                    'options': f.options or [],
                    'value': str(submitted),
                })
            return render(request, 'dashboard/employee_create.html', {
                'form_templates': form_templates,
                'selected_form_template': form_template_id,
                'fields': field_defs,
            })

        try:
            # Create employee
            employee = Employee.objects.create(
                form_template_id=form_template_id,
                created_by=request.user,
                is_active=True
            )

            # Create field values
            saved_fields_count = 0
            for field in fields:
                if field.field_type == 'file':
                    # Handle file uploads directly from request.FILES
                    uploaded_file = request.FILES.get(f'field_{field.id}')
                    if uploaded_file:
                        # Save the file and store the path
                        from django.core.files.storage import default_storage
                        import uuid
                        file_name = f"{uuid.uuid4()}_{uploaded_file.name}"
                        file_path = default_storage.save(f"employee_files/{file_name}", uploaded_file)
                        EmployeeFieldValue.objects.create(employee=employee, field=field, value=file_path)
                        saved_fields_count += 1
                else:
                    # Handle regular form fields
                    raw_value = field_values_data.get(str(field.id))
                    if raw_value is not None:
                        EmployeeFieldValue.objects.create(employee=employee, field=field, value=str(raw_value))
                        saved_fields_count += 1

            AuditLog.objects.create(
                employee=employee,
                action='create',
                performed_by=request.user,
                changes={'created': True},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            messages.success(request, 'Employee created successfully')
            return redirect('employee_management')
        except Exception as e:
            messages.error(request, f"Could not create employee: {e}")
            form_templates = FormTemplate.objects.order_by('name')
            field_defs = []
            for f in fields.order_by('order', 'id'):
                submitted = field_values_data.get(str(f.id), '')
                field_defs.append({
                    'id': f.id,
                    'field_label': f.field_label,
                    'field_name': f.field_name,
                    'field_type': f.field_type,
                    'is_required': f.is_required,
                    'placeholder': f.placeholder or '',
                    'help_text': f.help_text or '',
                    'options': f.options or [],
                    'value': str(submitted),
                })
            return render(request, 'dashboard/employee_create.html', {
                'form_templates': form_templates,
                'selected_form_template': form_template_id,
                'fields': field_defs,
            })

    # GET: optionally render fields for selected template (no JS needed)
    form_templates = FormTemplate.objects.order_by('name')
    selected = request.GET.get('form_template')
    ctx = { 'form_templates': form_templates, 'selected_form_template': selected or '' }
    if selected:
        fields = FormField.objects.filter(form_template_id=selected).order_by('order', 'id')
        field_defs = []
        for f in fields:
            field_defs.append({
                'id': f.id,
                'field_label': f.field_label,
                'field_name': f.field_name,
                'field_type': f.field_type,
                'is_required': f.is_required,
                'placeholder': f.placeholder or '',
                'help_text': f.help_text or '',
                'options': f.options or [],
                'value': '',
            })
        ctx['fields'] = field_defs
    return render(request, 'dashboard/employee_create.html', ctx)


@login_required
def employee_edit(request, employee_id):
    """Employee edit page"""
    employee = Employee.objects.select_related('form_template').prefetch_related('field_values__field').get(id=employee_id)

    if request.method == 'POST':
        field_values_json = request.POST.get('field_values_json')
        is_active = request.POST.get('is_active') == 'on'

        try:
            field_values_data = json.loads(field_values_json or '{}')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid field values data')
            return redirect('employee_edit', employee_id=employee_id)

        employee.is_active = is_active
        employee.save()

        fields = FormField.objects.filter(form_template=employee.form_template)
        for field in fields:
            raw_value = field_values_data.get(str(field.id))
            if raw_value is None:
                continue
            efv, _ = EmployeeFieldValue.objects.get_or_create(employee=employee, field=field)
            if field.field_type == 'file' and raw_value:
                efv.file_value = raw_value
                efv.value = None
            else:
                efv.value = str(raw_value)
                efv.file_value = None
            efv.save()

        AuditLog.objects.create(
            employee=employee,
            action='update',
            performed_by=request.user,
            changes={'updated': True},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

        messages.success(request, 'Employee updated successfully')
        return redirect('employee_detail', employee_id=employee_id)

    # Build fields with current values for server-rendered form
    field_defs = []
    form_fields = FormField.objects.filter(form_template=employee.form_template).order_by('order', 'id')
    value_by_field_id = {fv.field_id: fv for fv in employee.field_values.all()}
    for f in form_fields:
        current = value_by_field_id.get(f.id)
        current_value = ''
        if current:
            current_value = current.value or getattr(current.file_value, 'name', '') or ''
        field_defs.append({
            'id': f.id,
            'field_label': f.field_label,
            'field_name': f.field_name,
            'field_type': f.field_type,
            'is_required': f.is_required,
            'placeholder': f.placeholder or '',
            'help_text': f.help_text or '',
            'options': f.options or [],
            'value': current_value,
        })

    return render(request, 'dashboard/employee_edit.html', {
        'employee_id': employee_id,
        'employee_obj': employee,
        'fields': field_defs,
    })


@login_required
def employee_detail(request, employee_id):
    """Employee detail page"""
    employee = Employee.objects.select_related('form_template').prefetch_related('field_values__field').get(id=employee_id)
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        AuditLog.objects.create(
            employee=employee,
            action='delete',
            performed_by=request.user,
            changes={'deleted': True},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        employee.delete()
        messages.success(request, 'Employee deleted successfully')
        return redirect('employee_management')
    audit_logs = AuditLog.objects.filter(employee=employee).order_by('-timestamp')[:10]
    return render(request, 'dashboard/employee_detail.html', {
        'employee_id': employee_id,
        'employee_obj': employee,
        'audit_logs': audit_logs,
    })


@login_required
def audit_logs(request):
    """Audit logs page"""
    action = request.GET.get('action')
    employee_id = request.GET.get('employee')
    date_from = request.GET.get('timestamp__gte')
    date_to = request.GET.get('timestamp__lte')

    logs = AuditLog.objects.select_related('employee', 'performed_by').all()
    if action:
        logs = logs.filter(action=action)
    if employee_id:
        logs = logs.filter(employee_id=employee_id)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    logs = logs.order_by('-timestamp')[:100]
    employees = Employee.objects.order_by('-created_at')[:200]
    return render(request, 'dashboard/audit_logs.html', {
        'logs': logs,
        'employees': employees,
        'filters': {
            'action': action or '',
            'employee': employee_id or '',
            'timestamp__gte': date_from or '',
            'timestamp__lte': date_to or ''
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """Logout view"""
    from django.contrib.auth import logout
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})
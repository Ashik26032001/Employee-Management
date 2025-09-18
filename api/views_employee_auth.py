from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db import transaction
import json

from .models import Employee, EmployeeFieldValue, FormField, AuditLog
from .serializers import EmployeeSerializer


class EmployeeRegistrationView(APIView):
    """Employee registration endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            
            # Debug: Log the received data
            print(f"Received data: {data}")
            print(f"Data type: {type(data)}")
            
            # Validate required fields
            required_fields = ['username', 'password', 'form_template_id']
            for field in required_fields:
                if field not in data:
                    return Response({
                        'error': f'{field} is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            username = data['username']
            password = data['password']
            form_template_id = data['form_template_id']
            
            # Handle field_values - collect from different possible sources
            field_values = {}
            
            # Method 1: Check if field_values is provided as JSON string
            if 'field_values' in data:
                field_values_data = data['field_values']
                if isinstance(field_values_data, str):
                    try:
                        field_values = json.loads(field_values_data)
                    except json.JSONDecodeError:
                        # If it's not JSON, ignore it and use method 2
                        pass
                elif isinstance(field_values_data, dict):
                    field_values = field_values_data
            
            # Method 2: Collect all field_* parameters (for form-data)
            for key, value in data.items():
                if key.startswith('field_'):
                    field_id = key.replace('field_', '')
                    field_values[field_id] = value
            
            # Check if username already exists
            if Employee.objects.filter(username=username).exists():
                return Response({
                    'error': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate form template exists
            try:
                from .models import FormTemplate
                form_template = FormTemplate.objects.get(id=form_template_id)
            except FormTemplate.DoesNotExist:
                return Response({
                    'error': 'Invalid form template'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate required fields from form template
            form_fields = FormField.objects.filter(form_template_id=form_template_id, is_required=True)
            validation_errors = []
            
            for field in form_fields:
                field_value = field_values.get(str(field.id), '')
                if not field_value or (isinstance(field_value, str) and field_value.strip() == ''):
                    validation_errors.append(f"{field.field_label} is required")
            
            if validation_errors:
                return Response({
                    'error': 'Validation failed',
                    'details': validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create employee with transaction
            with transaction.atomic():
                # Create employee
                employee = Employee.objects.create(
                    username=username,
                    form_template_id=form_template_id,
                    is_employee_active=True,
                    created_by=request.user if hasattr(request, 'user') and request.user.is_authenticated else None
                )
                
                # Set password
                employee.set_password(password)
                employee.save()
                
                # Create field values
                for field_id, value in field_values.items():
                    try:
                        field = FormField.objects.get(id=field_id, form_template=form_template)
                        EmployeeFieldValue.objects.create(
                            employee=employee,
                            field=field,
                            value=str(value)
                        )
                    except FormField.DoesNotExist:
                        continue
                
                # Create audit log
                AuditLog.objects.create(
                    employee=employee,
                    action='create',
                    performed_by=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                    changes={'registration': True}
                )
            
            # Return success response
            serializer = EmployeeSerializer(employee)
            return Response({
                'message': 'Employee registered successfully',
                'employee': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': 'Registration failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeLoginView(APIView):
    """Employee login endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            if 'username' not in data or 'password' not in data:
                return Response({
                    'error': 'Username and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            username = data['username']
            password = data['password']
            
            # Find employee by username
            try:
                employee = Employee.objects.get(username=username, is_employee_active=True)
            except Employee.DoesNotExist:
                return Response({
                    'error': 'Invalid username or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check password
            if not employee.check_password(password):
                return Response({
                    'error': 'Invalid username or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Update last login
            employee.last_login = timezone.now()
            employee.save()
            
            # Create audit log
            AuditLog.objects.create(
                employee=employee,
                action='view',
                performed_by=None,  # Employee login doesn't have a User object
                changes={'login': True}
            )
            
            # Return employee data
            serializer = EmployeeSerializer(employee)
            return Response({
                'message': 'Login successful',
                'employee': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Login failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeChangePasswordView(APIView):
    """Employee password change endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['username', 'current_password', 'new_password']
            for field in required_fields:
                if field not in data:
                    return Response({
                        'error': f'{field} is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            username = data['username']
            current_password = data['current_password']
            new_password = data['new_password']
            
            # Validate new password
            if len(new_password) < 6:
                return Response({
                    'error': 'New password must be at least 6 characters long'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find employee
            try:
                employee = Employee.objects.get(username=username, is_employee_active=True)
            except Employee.DoesNotExist:
                return Response({
                    'error': 'Invalid username'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Verify current password
            if not employee.check_password(current_password):
                return Response({
                    'error': 'Current password is incorrect'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Update password
            employee.set_password(new_password)
            employee.save()
            
            # Create audit log
            AuditLog.objects.create(
                employee=employee,
                action='update',
                performed_by=None,  # Employee password change doesn't have a User object
                changes={'password_changed': True}
            )
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Password change failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def employee_profile(request, employee_id):
    """Get employee profile by ID"""
    try:
        employee = Employee.objects.get(employee_id=employee_id, is_employee_active=True)
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data)
    except Employee.DoesNotExist:
        return Response({
            'error': 'Employee not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Failed to fetch employee profile',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def employee_list(request):
    """Get list of active employees"""
    try:
        employees = Employee.objects.filter(is_employee_active=True, is_active=True)
        serializer = EmployeeSerializer(employees, many=True)
        return Response({
            'employees': serializer.data,
            'count': employees.count()
        })
    except Exception as e:
        return Response({
            'error': 'Failed to fetch employees',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

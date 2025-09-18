from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
import uuid


class UserProfile(models.Model):
    """Extended user profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class FormTemplate(models.Model):
    """Dynamic form template model"""
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('date', 'Date'),
        ('password', 'Password'),
        ('textarea', 'Text Area'),
        ('select', 'Select'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
        ('file', 'File Upload'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='form_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class FormField(models.Model):
    """Individual fields within a form template"""
    form_template = models.ForeignKey(FormTemplate, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FormTemplate.FIELD_TYPES)
    field_label = models.CharField(max_length=200)
    is_required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=200, blank=True, null=True)
    help_text = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    options = models.JSONField(blank=True, null=True, help_text="For select, radio, checkbox options")
    validation_rules = models.JSONField(blank=True, null=True, help_text="Custom validation rules")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['form_template', 'field_name']

    def __str__(self):
        return f"{self.form_template.name} - {self.field_label}"


class Employee(models.Model):
    """Employee model with dynamic fields and authentication"""
    employee_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    form_template = models.ForeignKey(FormTemplate, on_delete=models.CASCADE, related_name='employees')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_employees', null=True, blank=True)
    
    # Employee authentication fields
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)  # Will store hashed password
    is_employee_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Employee {self.employee_id}"

    @property
    def employee_name(self):
        """Get employee name from dynamic fields"""
        name_field = self.field_values.filter(field__field_name__icontains='name').first()
        if name_field:
            return name_field.value
        return f"Employee {self.employee_id}"
    
    def set_password(self, raw_password):
        """Set password for employee"""
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check password for employee"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)


class EmployeeFieldValue(models.Model):
    """Dynamic field values for employees"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='field_values')
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='employee_values')
    value = models.TextField(blank=True, null=True)
    file_value = models.FileField(upload_to='employee_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'field']

    def __str__(self):
        return f"{self.employee.employee_name} - {self.field.field_label}: {self.value}"


class AuditLog(models.Model):
    """Audit trail for employee operations"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=10, choices=ACTION_TYPES)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    changes = models.JSONField(blank=True, null=True, help_text="Field changes made")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        performed_by_name = self.performed_by.username if self.performed_by else "System"
        return f"{self.action.title()} {self.employee.employee_name} by {performed_by_name}"
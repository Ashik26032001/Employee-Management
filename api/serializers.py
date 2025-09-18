from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, FormTemplate, FormField, Employee, EmployeeFieldValue, AuditLog
from dashboard.models import DashboardSettings, SavedSearch, Notification


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=15, required=False)
    address = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'phone_number', 'address']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        password_confirm = validated_data.pop('password_confirm')
        phone_number = validated_data.pop('phone_number', None)
        address = validated_data.pop('address', None)

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create user profile
        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            address=address
        )

        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class FormFieldSerializer(serializers.ModelSerializer):
    """Serializer for form fields"""
    class Meta:
        model = FormField
        fields = ['id', 'field_name', 'field_type', 'field_label', 'is_required', 'placeholder', 'help_text', 'order', 'options', 'validation_rules']
        read_only_fields = ['id']


class FormTemplateSerializer(serializers.ModelSerializer):
    """Serializer for form templates"""
    fields = FormFieldSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = FormTemplate
        fields = ['id', 'name', 'description', 'created_by', 'created_by_username', 'created_at', 'updated_at', 'is_active', 'fields', 'employee_count']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employee_count(self, obj):
        return obj.employees.count()


class FormTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating form templates with fields"""
    fields_data = FormFieldSerializer(many=True, write_only=True)

    class Meta:
        model = FormTemplate
        fields = ['name', 'description', 'fields_data']

    def create(self, validated_data):
        fields_data = validated_data.pop('fields_data')
        form_template = FormTemplate.objects.create(**validated_data)
        
        for field_data in fields_data:
            FormField.objects.create(form_template=form_template, **field_data)
        
        return form_template


class EmployeeFieldValueSerializer(serializers.ModelSerializer):
    """Serializer for employee field values"""
    field_name = serializers.CharField(source='field.field_name', read_only=True)
    field_label = serializers.CharField(source='field.field_label', read_only=True)
    field_type = serializers.CharField(source='field.field_type', read_only=True)

    class Meta:
        model = EmployeeFieldValue
        fields = ['id', 'field', 'field_name', 'field_label', 'field_type', 'value', 'file_value']
        read_only_fields = ['id']


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for employees"""
    field_values = EmployeeFieldValueSerializer(many=True, read_only=True)
    form_template_name = serializers.CharField(source='form_template.name', read_only=True)
    created_by_username = serializers.SerializerMethodField()
    employee_name = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'username', 'form_template', 'form_template_name', 'created_by', 'created_by_username', 'created_at', 'updated_at', 'is_active', 'is_employee_active', 'last_login', 'field_values', 'employee_name']
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at', 'last_login']

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employees"""
    field_values_data = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Employee
        fields = ['form_template', 'field_values_data', 'is_active']

    def create(self, validated_data):
        field_values_data = validated_data.pop('field_values_data', {})
        employee = Employee.objects.create(**validated_data)
        
        # Create field values
        if field_values_data:
            for field_id, value in field_values_data.items():
                try:
                    field = FormField.objects.get(id=field_id)
                    if field.field_type == 'file' and value:
                        # Handle file upload
                        EmployeeFieldValue.objects.create(
                            employee=employee,
                            field=field,
                            file_value=value
                        )
                    else:
                        EmployeeFieldValue.objects.create(
                            employee=employee,
                            field=field,
                            value=value
                        )
                except FormField.DoesNotExist:
                    continue
        
        return employee

    def update(self, instance, validated_data):
        field_values_data = validated_data.pop('field_values_data', {})
        
        # Update employee
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update field values
        if field_values_data:
            for field_id, value in field_values_data.items():
                try:
                    field = FormField.objects.get(id=field_id)
                    field_value, created = EmployeeFieldValue.objects.get_or_create(
                        employee=instance,
                        field=field
                    )
                    
                    if field.field_type == 'file' and value:
                        field_value.file_value = value
                        field_value.value = None
                    else:
                        field_value.value = value
                        field_value.file_value = None
                    
                    field_value.save()
                except FormField.DoesNotExist:
                    continue
        
        return instance


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'employee', 'employee_name', 'action', 'performed_by', 'performed_by_username', 'changes', 'timestamp', 'ip_address']
        read_only_fields = ['id', 'timestamp']


class DashboardSettingsSerializer(serializers.ModelSerializer):
    """Serializer for dashboard settings"""
    class Meta:
        model = DashboardSettings
        fields = ['id', 'default_form_template', 'items_per_page', 'theme', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SavedSearchSerializer(serializers.ModelSerializer):
    """Serializer for saved searches"""
    class Meta:
        model = SavedSearch
        fields = ['id', 'name', 'search_query', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    employee_name = serializers.CharField(source='related_employee.employee_name', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'related_employee', 'employee_name', 'created_at']
        read_only_fields = ['id', 'created_at']


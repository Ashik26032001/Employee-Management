from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, FormTemplate, FormField, Employee, EmployeeFieldValue, AuditLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    ordering = ['order']


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['name', 'description']
    inlines = [FormFieldInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ['field_label', 'field_name', 'field_type', 'form_template', 'order', 'is_required']
    list_filter = ['field_type', 'is_required', 'form_template']
    search_fields = ['field_label', 'field_name', 'form_template__name']
    ordering = ['form_template', 'order']


class EmployeeFieldValueInline(admin.TabularInline):
    model = EmployeeFieldValue
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'form_template', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'form_template', 'created_by']
    search_fields = ['employee_id', 'form_template__name']
    inlines = [EmployeeFieldValueInline]
    readonly_fields = ['employee_id', 'created_at', 'updated_at']


@admin.register(EmployeeFieldValue)
class EmployeeFieldValueAdmin(admin.ModelAdmin):
    list_display = ['employee', 'field', 'value', 'created_at']
    list_filter = ['field__field_type', 'created_at', 'employee__form_template']
    search_fields = ['value', 'employee__employee_id', 'field__field_label']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp', 'performed_by']
    search_fields = ['employee__employee_id', 'performed_by__username']
    readonly_fields = ['timestamp']


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
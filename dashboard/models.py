from django.db import models
from django.contrib.auth.models import User
from api.models import FormTemplate, Employee, FormField, EmployeeFieldValue


class DashboardSettings(models.Model):
    """Dashboard configuration settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_settings')
    default_form_template = models.ForeignKey(FormTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    items_per_page = models.PositiveIntegerField(default=20)
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Dashboard Settings"


class SavedSearch(models.Model):
    """Saved search queries for employees"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    search_query = models.JSONField(help_text="Search parameters and filters")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    related_employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
from django.urls import path
from . import views
from . import views_employee_auth

urlpatterns = [
    # Admin/Manager routes
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('form-builder/', views.form_builder, name='form_builder'),
    path('employees/', views.employee_management, name='employee_management'),
    path('employees/export/', views.employee_export, name='employee_export'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<str:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<str:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('logout/', views.logout_view, name='logout'),
    
    # Employee authentication routes
    path('employee/login/', views_employee_auth.employee_login, name='employee_login'),
    path('employee/register/', views_employee_auth.employee_register, name='employee_register'),
    path('employee/change-password/', views_employee_auth.employee_change_password, name='employee_change_password'),
    path('employee/dashboard/', views_employee_auth.employee_dashboard, name='employee_dashboard'),
    path('employee/list/', views_employee_auth.employee_list_view, name='employee_list_view'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView, UserRegistrationView, ChangePasswordView, ProfileView
)
from .views_forms import FormTemplateViewSet
from .views_employees import EmployeeViewSet, AuditLogViewSet
from .views_dashboard import (
    DashboardSettingsView, SavedSearchViewSet, NotificationViewSet, 
    FileUploadView, dashboard_stats
)
from .views_employee_auth import (
    EmployeeRegistrationView, EmployeeLoginView, EmployeeChangePasswordView,
    employee_profile, employee_list
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'form-templates', FormTemplateViewSet, basename='form-template')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'saved-searches', SavedSearchViewSet, basename='saved-search')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Admin/Manager Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/profile/', ProfileView.as_view(), name='user_profile'),
    
    # Employee Authentication endpoints
    path('employee/auth/register/', EmployeeRegistrationView.as_view(), name='employee_register'),
    path('employee/auth/login/', EmployeeLoginView.as_view(), name='employee_login'),
    path('employee/auth/change-password/', EmployeeChangePasswordView.as_view(), name='employee_change_password'),
    path('employee/profile/<str:employee_id>/', employee_profile, name='employee_profile'),
    path('employee/list/', employee_list, name='employee_list'),
    
    # Dashboard endpoints
    path('dashboard/settings/', DashboardSettingsView.as_view(), name='dashboard_settings'),
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('dashboard/upload/', FileUploadView.as_view(), name='file_upload'),
    
    # Include router URLs
    path('', include(router.urls)),
]
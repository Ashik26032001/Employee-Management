from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from api.models import FormTemplate, Employee


def employee_login(request):
    """Employee login page"""
    return render(request, 'dashboard/employee_login.html')


def employee_register(request):
    """Employee registration page"""
    form_templates = FormTemplate.objects.filter(is_active=True).order_by('name')
    return render(request, 'dashboard/employee_register.html', {
        'form_templates': form_templates
    })


def employee_change_password(request):
    """Employee change password page"""
    return render(request, 'dashboard/employee_change_password.html')


def employee_dashboard(request):
    """Employee dashboard after login"""
    # Check if employee is logged in via sessionStorage
    return render(request, 'dashboard/employee_dashboard.html')


def employee_list_view(request):
    """List all employees (for admin/managers)"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    employees = Employee.objects.filter(is_active=True, is_employee_active=True).order_by('-created_at')
    
    return render(request, 'dashboard/employee_list.html', {
        'employees': employees
    })


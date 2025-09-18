from rest_framework import generics, status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import uuid

from .models import FormTemplate, FormField, Employee, EmployeeFieldValue, AuditLog
from .serializers import (
    EmployeeSerializer, EmployeeCreateUpdateSerializer, EmployeeFieldValueSerializer,
    AuditLogSerializer
)


class EmployeeViewSet(viewsets.ModelViewSet):
    """Employee CRUD operations"""
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['form_template', 'is_active', 'created_by']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Employee.objects.filter(created_by=self.request.user)
        
        # Dynamic search based on field values
        search_query = self.request.query_params.get('search', None)
        if search_query:
            field_values = EmployeeFieldValue.objects.filter(
                value__icontains=search_query,
                employee__created_by=self.request.user
            )
            employee_ids = field_values.values_list('employee_id', flat=True)
            queryset = queryset.filter(id__in=employee_ids)
        
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
        # Create audit log
        AuditLog.objects.create(
            employee=serializer.instance,
            action='create',
            performed_by=self.request.user,
            ip_address=self.get_client_ip()
        )

    def perform_update(self, serializer):
        old_values = {}
        if self.action == 'update':
            # Get old values for audit
            old_values = {fv.field.field_name: fv.value for fv in serializer.instance.field_values.all()}
        
        serializer.save()
        
        # Create audit log
        AuditLog.objects.create(
            employee=serializer.instance,
            action='update',
            performed_by=self.request.user,
            changes={'old_values': old_values},
            ip_address=self.get_client_ip()
        )

    def perform_destroy(self, instance):
        # Create audit log before deletion
        AuditLog.objects.create(
            employee=instance,
            action='delete',
            performed_by=self.request.user,
            ip_address=self.get_client_ip()
        )
        instance.delete()

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=True, methods=['get'])
    def field_values(self, request, pk=None):
        """Get field values for a specific employee"""
        employee = self.get_object()
        field_values = employee.field_values.all()
        serializer = EmployeeFieldValueSerializer(field_values, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for employees"""
        query_params = request.query_params
        form_template_id = query_params.get('form_template')
        search_terms = query_params.get('search_terms', '').split(',')
        
        queryset = Employee.objects.filter(created_by=request.user)
        
        if form_template_id:
            queryset = queryset.filter(form_template_id=form_template_id)
        
        if search_terms:
            field_value_queries = Q()
            for term in search_terms:
                if term.strip():
                    field_value_queries |= Q(
                        field_values__value__icontains=term.strip()
                    )
            queryset = queryset.filter(field_value_queries).distinct()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log view (read-only)"""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'performed_by', 'employee']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        return AuditLog.objects.filter(employee__created_by=self.request.user)


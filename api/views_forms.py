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
    FormTemplateSerializer, FormTemplateCreateSerializer, FormFieldSerializer,
    EmployeeSerializer, EmployeeCreateUpdateSerializer, EmployeeFieldValueSerializer,
    AuditLogSerializer
)


class FormTemplateViewSet(viewsets.ModelViewSet):
    """Form template CRUD operations"""
    serializer_class = FormTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active', 'created_by']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return FormTemplate.objects.filter(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return FormTemplateCreateSerializer
        return FormTemplateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def fields(self, request, pk=None):
        """Get fields for a specific form template"""
        form_template = self.get_object()
        fields = form_template.fields.all()
        serializer = FormFieldSerializer(fields, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_field(self, request, pk=None):
        """Add a field to form template"""
        form_template = self.get_object()
        serializer = FormFieldSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(form_template=form_template)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def reorder_fields(self, request, pk=None):
        """Reorder fields in form template"""
        form_template = self.get_object()
        field_orders = request.data.get('field_orders', [])
        
        for field_data in field_orders:
            field_id = field_data.get('id')
            order = field_data.get('order')
            try:
                field = FormField.objects.get(id=field_id, form_template=form_template)
                field.order = order
                field.save()
            except FormField.DoesNotExist:
                continue
        
        return Response({'message': 'Fields reordered successfully'})


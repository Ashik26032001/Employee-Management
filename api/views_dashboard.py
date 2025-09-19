from rest_framework import generics, status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
import uuid

from .models import Employee, AuditLog
from .serializers import (
    DashboardSettingsSerializer, SavedSearchSerializer, NotificationSerializer
)
from dashboard.models import DashboardSettings, SavedSearch, Notification,FormTemplate


class DashboardSettingsView(APIView):
    """Dashboard settings management"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings, created = DashboardSettings.objects.get_or_create(user=request.user)
        serializer = DashboardSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        settings, created = DashboardSettings.objects.get_or_create(user=request.user)
        serializer = DashboardSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavedSearchViewSet(viewsets.ModelViewSet):
    """Saved search management"""
    serializer_class = SavedSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notification management (read-only for now)"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})


class FileUploadView(APIView):
    """Handle file uploads for employee fields"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file
        file_name = f"{uuid.uuid4()}_{file.name}"
        file_path = default_storage.save(f"employee_files/{file_name}", file)
        
        return Response({
            'file_path': file_path,
            'file_name': file.name,
            'file_size': file.size
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    user = request.user
    
    stats = {
        'total_employees': Employee.objects.filter(created_by=user).count(),
        'total_form_templates': FormTemplate.objects.filter(created_by=user).count(),
        'active_employees': Employee.objects.filter(created_by=user, is_active=True).count(),
        'recent_employees': Employee.objects.filter(created_by=user).order_by('-created_at')[:5].count(),
        'unread_notifications': Notification.objects.filter(user=user, is_read=False).count(),
    }
    
    return Response(stats)


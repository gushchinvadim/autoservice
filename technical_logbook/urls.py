from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .admin_views import import_parts_view, import_maintenance_view, bulk_add_norms_view

router = DefaultRouter()
router.register(r'cars', views.CarViewSet, basename='car')
router.register(r'tasks', views.MaintenanceTaskViewSet, basename='task')
router.register(r'records', views.MaintenanceRecordViewSet, basename='record')
router.register(r'spareparts', views.SparePartViewSet, basename='sparepart')
router.register(r'car-models', views.CarModelViewSet, basename='carmodel')

urlpatterns = [
    path('', include(router.urls)),
    # Перенесли импорт сюда, чтобы они были доступны как /api/import/...
    path('import/parts/', import_parts_view, name='import_parts'),
    path('import/maintenance/', import_maintenance_view, name='import_maintenance'),
    path('bulk-add-norms/', bulk_add_norms_view, name='bulk_add_norms'),
] # ← Убрана опечатка "].     ," из вашего исходника
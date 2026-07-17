from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'cars', views.CarViewSet, basename='car')
router.register(r'tasks', views.MaintenanceTaskViewSet, basename='task')
router.register(r'records', views.MaintenanceRecordViewSet, basename='record')
router.register(r'spareparts', views.SparePartViewSet, basename='sparepart')
router.register(r'car-models', views.CarModelViewSet, basename='carmodel')

urlpatterns = [
    path('', include(router.urls)),

]
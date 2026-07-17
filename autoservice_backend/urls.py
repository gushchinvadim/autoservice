from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from technical_logbook.admin_views import import_parts_view, import_maintenance_view, bulk_add_norms_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # === ВАЖНО: Префикс 'admin/' гарантирует правильный маршрут через Nginx ===
    path('admin/import/parts/', import_parts_view, name='import_parts'),
    path('admin/import/maintenance/', import_maintenance_view, name='import_maintenance'),
    path('admin/bulk-add-norms/', bulk_add_norms_view, name='bulk_add_norms'),

    path('api/', include('technical_logbook.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
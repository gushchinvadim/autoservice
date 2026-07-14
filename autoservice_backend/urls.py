from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from technical_logbook.admin_views import import_parts_view, import_maintenance_view, bulk_add_norms_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('technical_logbook.urls')),

    # JWT токены
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Импорт из Excel (доступно через /import/parts/ и /import/maintenance/)
    path('import/parts/', import_parts_view, name='import_parts'),
    path('import/maintenance/', import_maintenance_view, name='import_maintenance'),
    path('bulk-add-norms/', bulk_add_norms_view, name='bulk_add_norms'),
]
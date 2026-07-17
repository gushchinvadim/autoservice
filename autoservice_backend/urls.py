from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Импортируем ваши view для импорта
from technical_logbook.admin_views import (
    import_parts_view,
    import_maintenance_view,
    bulk_add_norms_view
)

urlpatterns = [
    # 1. СНАЧАЛА кастомные пути, начинающиеся с /admin/
    path('admin/import/parts/', import_parts_view, name='import_parts'),
    path('admin/import/maintenance/', import_maintenance_view, name='import_maintenance'),
    path('admin/bulk-add-norms/', bulk_add_norms_view, name='bulk_add_norms'),

    # 2. ТОЛЬКО ПОТОМ стандартная админка (она перехватит всё остальное, что начинается с /admin/)
    path('admin/', admin.site.urls),

    # 3. API маршруты
    path('api/', include('technical_logbook.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
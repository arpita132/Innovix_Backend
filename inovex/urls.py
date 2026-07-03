from django.contrib import admin
from django.urls import path, include
from rbac.views import ensure_default_admin

# Programmatically initialize default superuser on startup
ensure_default_admin()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/rbac/', include('rbac.urls')),
]

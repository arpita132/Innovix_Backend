from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserLoginView, UserProfileView, UserManagementViewSet

router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user')

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('', include(router.urls)),
]

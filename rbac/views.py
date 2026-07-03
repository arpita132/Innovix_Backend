from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
import logging

from .models import UserProfile
from .serializers import UserSerializer, UserCreateSerializer
from .permissions import IsAdminRole

logger = logging.getLogger(__name__)

class UserLoginView(APIView):
    permission_classes = []  # Public endpoint

    def post(self, request, *args, **kwargs):
        username_or_email = request.data.get('username')
        password = request.data.get('password')

        if not username_or_email or not password:
            return Response({'error': 'Please provide both username/email and password.'}, status=status.HTTP_400_BAD_REQUEST)

        # Try authenticating by username first
        user = authenticate(username=username_or_email, password=password)
        if not user:
            # Try finding user by email
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Get role
        try:
            role = user.profile.role
        except UserProfile.DoesNotExist:
            role = 'CONTENT_CREATOR'  # fallback

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': role
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by('id')
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Return serialized data using UserSerializer
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Return serialized data using UserSerializer
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

def ensure_default_admin():
    from django.db.utils import ProgrammingError, OperationalError
    User = get_user_model()
    try:
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('AdminPassword@123')
            admin_user.save()
            
        profile, p_created = UserProfile.objects.get_or_create(user=admin_user)
        if profile.role != 'ADMIN':
            profile.role = 'ADMIN'
            profile.save()
    except (ProgrammingError, OperationalError):
        # Database tables might not be created yet during migrations
        pass

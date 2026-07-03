from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_superuser', 'is_staff')

    def get_role(self, obj):
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            return None

class UserCreateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'role', 'is_staff', 'is_superuser')
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        role = validated_data.pop('role', 'CONTENT_CREATOR')
        password = validated_data.pop('password')
        
        # Determine is_staff and is_superuser based on role
        is_staff = validated_data.get('is_staff', False)
        is_superuser = validated_data.get('is_superuser', False)
        
        if role == 'ADMIN':
            is_superuser = True
            is_staff = True
        elif role == 'HR':
            is_staff = True
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        
        # Since the signal creates the profile, we retrieve/update it
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()
        
        user.refresh_from_db()
        return user

    def update(self, instance, validated_data):
        role = validated_data.pop('role', None)
        password = validated_data.pop('password', None)
        
        # Update normal user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        
        if role:
            if role == 'ADMIN':
                instance.is_superuser = True
                instance.is_staff = True
            elif role == 'HR':
                instance.is_staff = True
                instance.is_superuser = False
            else:
                instance.is_staff = False
                instance.is_superuser = False
            instance.save()
            
            profile, created = UserProfile.objects.get_or_create(user=instance)
            profile.role = role
            profile.save()
            
        instance.refresh_from_db()
        return instance

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserPhoto

User = get_user_model()

class UserPhotoSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = UserPhoto
        fields = ('id', 'photo', 'photo_url', 'description', 'uploaded_at', 'is_public')
        read_only_fields = ('id', 'uploaded_at')

    def get_photo_url(self, obj):
        if obj.photo:
            return self.context['request'].build_absolute_uri(obj.photo.url)
        return None

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    photos = UserPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'avatar', 'avatar_url', 'photos', 'is_superuser')
        read_only_fields = ('id', 'email', 'is_superuser')

    def get_avatar_url(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None 
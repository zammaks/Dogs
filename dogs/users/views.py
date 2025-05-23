from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, UserPhotoSerializer
from .models import UserPhoto

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        # Удаляем токен пользователя
        if hasattr(user, 'auth_token'):
            user.auth_token.delete()
        # Удаляем пользователя
        user.delete()
        return Response({"message": "Аккаунт успешно удален"}, status=status.HTTP_204_NO_CONTENT)

class UserPhotoListCreateView(generics.ListCreateAPIView):
    serializer_class = UserPhotoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def get_queryset(self):
        return UserPhoto.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class UserPhotoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserPhotoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def get_queryset(self):
        return UserPhoto.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context 
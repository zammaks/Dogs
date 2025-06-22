from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, UserPhotoSerializer
from .models import UserPhoto, User
from main.tasks import send_profile_update_notification
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_strategy, load_backend, psa
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden, AuthCanceled
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
import json
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        return user

class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

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
        
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            # Отправляем задачу в Celery
            try:
                send_profile_update_notification.delay(request.user.id)
            except Exception as e:
                print(f"Error sending notification task: {e}")
        return response

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

@api_view(['POST'])
@permission_classes([AllowAny])
def yandex_auth(request):
    """
    Обработчик для авторизации через Яндекс
    """
    code = request.data.get('code')
    
    if not code:
        return Response(
            {'error': 'Код авторизации не предоставлен'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        strategy = load_strategy(request)
        backend = load_backend(
            strategy=strategy,
            name='yandex-oauth2',
            redirect_uri='http://localhost:5173/auth/yandex/callback'
        )

        try:
            user = backend.do_auth(code)
        except Exception as e:
            return Response(
                {'error': f'Ошибка авторизации Яндекс: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if user:
            try:
                # Если пользователь уже существует, обновляем его данные
                if isinstance(user, User):
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'token': str(refresh.access_token),
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_superuser': user.is_superuser
                        }
                    })
                else:
                    return Response(
                        {'error': 'Неверный тип пользователя'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {'error': f'Ошибка при создании токена: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'Пользователь не найден'}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
    except (MissingBackend, AuthTokenError) as e:
        return Response(
            {'error': f'Ошибка аутентификации: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Неизвестная ошибка: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def yandex_callback(request):
    """
    Обработчик для callback'а от Яндекс OAuth2
    Поддерживает как GET, так и POST запросы
    """
    try:
        # Получаем параметры из GET или POST запроса
        if request.method == 'GET':
            code = request.GET.get('code')
            state = request.GET.get('state')
            logger.info(f"GET request - code: {code}, state: {state}")
        else:  # POST
            code = request.data.get('code')
            state = request.data.get('state')
            logger.info(f"POST request - code: {code}, state: {state}")

        if not code:
            logger.error("Код авторизации не предоставлен")
            return Response(
                {'error': 'Код авторизации не предоставлен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if not state:
            logger.error("Параметр state не предоставлен")
            return Response(
                {'error': 'Параметр state не предоставлен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Прямой обмен кода на токен через API Яндекса
        logger.info("Обмениваем код на токен доступа через API Яндекса")
        
        token_url = 'https://oauth.yandex.ru/token'
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': '5549c064b08e4a7b8be4f77568ac559a',
            'client_secret': 'cc1cfdbcce8e407f8f0be86589c491d0',
            'redirect_uri': 'http://localhost:8000/api/auth/yandex/callback/'
        }
        
        try:
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()
            
            access_token = token_info.get('access_token')
            if not access_token:
                logger.error("Токен доступа не найден в ответе Яндекса")
                return Response(
                    {'error': 'Токен доступа не найден'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            logger.info("Токен доступа получен успешно")
            
            # Получаем информацию о пользователе
            user_info_url = 'https://login.yandex.ru/info'
            headers = {'Authorization': f'OAuth {access_token}'}
            user_response = requests.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            logger.info(f"Получена информация о пользователе: {user_info.get('real_name', 'Unknown')}")
            
            # Получаем или создаем пользователя
            email = user_info.get('default_email')
            if not email:
                logger.error("Email пользователя не найден")
                return Response(
                    {'error': 'Email пользователя не найден'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Ищем существующего пользователя или создаем нового
            try:
                user = User.objects.get(email=email)
                logger.info(f"Найден существующий пользователь: {user.email}")
            except User.DoesNotExist:
                # Создаем нового пользователя
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=user_info.get('first_name', ''),
                    last_name=user_info.get('last_name', ''),
                    password=None  # Пользователи OAuth не имеют пароля
                )
                logger.info(f"Создан новый пользователь: {user.email}")
            
            # Создаем JWT токены
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обмене кода на токен: {str(e)}")
            return Response(
                {'error': f'Ошибка при обмене кода на токен: {str(e)}'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
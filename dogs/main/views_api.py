from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.db.models import Q, Count, Avg
from .models import DogSitter, Booking, User, Animal, Service, Review
from .serializers import DogSitterSerializer, BookingSerializer, UserSerializer, AnimalSerializer, ServiceSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .permissions import IsSuperUser
from .views_annotations import (
    get_dogsitter_statistics,
    get_animal_statistics,
    get_booking_analytics,
    get_user_statistics,
    get_dogsitter_with_ratings,
    get_bookings_with_ratings
)

def index(request):
    return render(request, 'main/index.html')

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    try:
        user = User.objects.create(
            email=request.data.get('email'),
            username=request.data.get('email'),  # Используем email как username
            first_name=request.data.get('first_name'),
            last_name=request.data.get('last_name')
        )
        user.set_password(request.data.get('password'))
        user.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    except IntegrityError:
        return Response(
            {'message': 'Пользователь с таким email уже существует'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'message': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    print(f"Login attempt for email: {email}")
    
    # Пробуем аутентифицировать, используя email как username
    user = authenticate(username=email, password=password)
    
    # Если не получилось, ищем пользователя по email и пробуем аутентифицировать по его username
    if user is None:
        try:
            user_obj = User.objects.get(email=email)
            print(f"Found user by email: {user_obj}, is_superuser: {user_obj.is_superuser}")
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
    
    if user is not None:
        print(f"User authenticated: {user}, is_superuser: {user.is_superuser}")
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        print(f"Serialized user data: {user_data}")
        return Response({
            'token': str(refresh.access_token),
            'user': user_data
        })
    else:
        print("Authentication failed")
        return Response(
            {'message': 'Неверный email или пароль'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

class DogSitterViewSet(viewsets.ModelViewSet):
    serializer_class = DogSitterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Возвращает queryset с аннотированными полями рейтинга
        """
        return get_dogsitter_with_ratings()

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsSuperUser()]
        return super().get_permissions()

    @action(detail=True, methods=['post'], permission_classes=[IsSuperUser])
    def block(self, request, pk=None):
        dogsitter = self.get_object()
        dogsitter.is_blocked = True
        dogsitter.save()
        return Response({'status': 'dogsitter blocked'})

    @action(detail=True, methods=['post'], permission_classes=[IsSuperUser])
    def unblock(self, request, pk=None):
        dogsitter = self.get_object()
        dogsitter.is_blocked = False
        dogsitter.save()
        return Response({'status': 'dogsitter unblocked'})

    def destroy(self, request, *args, **kwargs):
        dogsitter = self.get_object()
        dogsitter.delete()
        return Response({'status': 'dogsitter deleted'}, status=204)

    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        """
        Детальная информация о рейтингах догситтера
        """
        dogsitter = self.get_object()
        serializer = self.get_serializer(dogsitter)
        return Response(serializer.data)

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Возвращает queryset с аннотированными полями отзывов
        """
        return get_bookings_with_ratings()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def review_details(self, request, pk=None):
        """
        Детальная информация об отзыве к бронированию
        """
        booking = self.get_object()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, pk):
    try:
        booking = Booking.objects.get(pk=pk, user=request.user)
        if booking.status == 'pending':
            booking.status = 'cancelled'
            booking.save()
            return Response({'status': 'cancelled'})
        return Response(
            {'error': 'Booking cannot be cancelled'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

class AnimalViewSet(viewsets.ModelViewSet):
    serializer_class = AnimalSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Animal.objects.all().select_related('user')
        return Animal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
def get_statistics(request):
    """
    Получение общей статистики с использованием аннотаций
    """
    # Получаем статистику по всем моделям
    dogsitters_stats = get_dogsitter_statistics()
    animals_stats = get_animal_statistics()
    bookings_stats = get_booking_analytics()
    users_stats = get_user_statistics()

    # Формируем статистику по догситтерам
    top_dogsitters = dogsitters_stats.order_by('-total_bookings')[:5].values(
        'user__first_name',
        'total_bookings',
        'active_bookings',
        'avg_rating',
        'total_earnings',
        'regular_clients',
        'success_rate',
        'main_pet_type'
    )

    # Статистика по животным
    popular_animals = animals_stats.order_by('-completed_bookings')[:5].values(
        'name',
        'type',
        'completed_bookings',
        'avg_booking_duration',
        'favorite_sitter',
        'days_since_last_booking',
        'total_services_cost'
    )

    # Статистика по бронированиям
    recent_bookings = bookings_stats.order_by('-start_date')[:5].values(
        'id',
        'duration',
        'animals_count',
        'price_per_day',
        'booking_status',
        'services_count',
        'services_total_cost',
        'booking_month',
        'booking_year'
    )

    # Статистика по пользователям
    active_users = users_stats.order_by('-total_spent')[:5].values(
        'first_name',
        'total_animals',
        'active_bookings',
        'total_spent',
        'avg_review_rating',
        'unique_dogsitters',
        'preferred_pet_size',
        'client_status'
    )

    return Response({
        'top_dogsitters': list(top_dogsitters),
        'popular_animals': list(popular_animals),
        'recent_bookings': list(recent_bookings),
        'active_users': list(active_users)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperUser])
def block_dogsitter(request, pk):
    """
    Блокировка/разблокировка догситтера (только для администраторов)
    """
    try:
        dogsitter = DogSitter.objects.get(pk=pk)
        action = request.path.split('/')[-2]  # Получаем 'block' или 'unblock' из URL
        
        if action == 'block':
            dogsitter.is_blocked = True
            dogsitter.save()
            return Response({'status': 'success', 'message': 'Догситтер заблокирован'})
        elif action == 'unblock':
            dogsitter.is_blocked = False
            dogsitter.save()
            return Response({'status': 'success', 'message': 'Догситтер разблокирован'})
        
        return Response(
            {'error': 'Неверное действие'},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except DogSitter.DoesNotExist:
        return Response(
            {'error': 'Догситтер не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
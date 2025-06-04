from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.db.models import Q, Count, Avg
from .models import DogSitter, Booking, User, Animal, Service, Review
from .serializers import DogSitterSerializer, BookingSerializer, UserSerializer, AnimalSerializer, ServiceSerializer
from rest_framework.parsers import MultiPartParser, FormParser

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
    
    user = authenticate(username=email, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    else:
        return Response(
            {'message': 'Неверный email или пароль'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

class DogSitterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DogSitter.objects.all()
    serializer_class = DogSitterSerializer
    permission_classes = [IsAuthenticated]

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
@permission_classes([AllowAny])
def get_statistics(request):
    """
    API endpoint для получения общей статистики
    """
    # Получаем статистику по бронированиям
    completed_bookings = Booking.objects.filter(status='completed').count()
    
    # Получаем количество догситтеров
    dogsitters = DogSitter.objects.all()
    dogsitters_count = dogsitters.count()
    
    # Простое вычисление среднего рейтинга
    total_rating = sum(sitter.rating for sitter in dogsitters)
    avg_rating = total_rating / dogsitters_count if dogsitters_count > 0 else 0
    
    return Response({
        'completed_bookings': completed_bookings,
        'dogsitters_count': dogsitters_count,
        'avg_rating': round(avg_rating, 1)
    }) 
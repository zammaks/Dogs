from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, DogSitter, Booking, Animal, Service, Review
from django.db.models import Count, Avg
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_superuser')
        read_only_fields = ('id', 'is_superuser')

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='booking.user', read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'text', 'rating', 'user', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

class DogSitterSerializer(serializers.ModelSerializer):
    # Добавляем поля пользователя
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    avatar = serializers.FileField(read_only=True)

    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)
    five_star_reviews = serializers.IntegerField(read_only=True)
    four_star_reviews = serializers.IntegerField(read_only=True)
    three_star_reviews = serializers.IntegerField(read_only=True)
    two_star_reviews = serializers.IntegerField(read_only=True)
    one_star_reviews = serializers.IntegerField(read_only=True)
    positive_reviews_percentage = serializers.FloatField(read_only=True)
    recent_reviews = serializers.IntegerField(read_only=True)

    # Дополнительные вычисляемые поля
    rating_distribution = serializers.SerializerMethodField()
    rating_summary = serializers.SerializerMethodField()

    class Meta:
        model = DogSitter
        fields = [
            'id', 'user', 'first_name', 'last_name', 'avatar',
            'experience_years', 'description',
            'average_rating', 'total_reviews',
            'five_star_reviews', 'four_star_reviews', 'three_star_reviews',
            'two_star_reviews', 'one_star_reviews',
            'positive_reviews_percentage', 'recent_reviews',
            'rating_distribution', 'rating_summary'
        ]

    def get_rating_distribution(self, obj):
        """
        Возвращает распределение оценок в процентах
        """
        total = obj.total_reviews or 1  # Избегаем деления на ноль
        return {
            '5_stars': (obj.five_star_reviews * 100) / total,
            '4_stars': (obj.four_star_reviews * 100) / total,
            '3_stars': (obj.three_star_reviews * 100) / total,
            '2_stars': (obj.two_star_reviews * 100) / total,
            '1_star': (obj.one_star_reviews * 100) / total
        }

    def get_rating_summary(self, obj):
        """
        Возвращает текстовое описание рейтинга
        """
        if not obj.total_reviews:
            return "Нет отзывов"
        
        return {
            'average': f"{obj.average_rating:.1f}",
            'total': obj.total_reviews,
            'positive_percentage': f"{obj.positive_reviews_percentage:.1f}%",
            'recent_month': obj.recent_reviews
        }

class AnimalSerializer(serializers.ModelSerializer):
    booking_count = serializers.SerializerMethodField()
    last_booking_date = serializers.SerializerMethodField()
    is_available_for_booking = serializers.SerializerMethodField()
    
    can_edit = serializers.SerializerMethodField()
    dogsitter_notes = serializers.SerializerMethodField()
    
    class Meta:
        model = Animal
        fields = ['id', 'name', 'type', 'breed', 'age', 'size', 'special_needs', 
                 'photo', 'booking_count', 'last_booking_date', 
                 'is_available_for_booking', 'can_edit', 'dogsitter_notes']

    def get_booking_count(self, obj):
        return obj.bookings.count()

    def get_last_booking_date(self, obj):
        last_booking = obj.bookings.order_by('-start_date').first()
        return last_booking.start_date if last_booking else None

    def get_is_available_for_booking(self, obj):
        today = timezone.now().date()
        current_booking = obj.bookings.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='confirmed'
        ).exists()
        return not current_booking and obj.is_available

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user == obj.user or request.user.is_staff

    def get_dogsitter_notes(self, obj):
        dogsitter_id = self.context.get('dogsitter_id')
        if not dogsitter_id:
            return None
            
        last_booking = obj.bookings.filter(
            dog_sitter_id=dogsitter_id
        ).order_by('-end_date').first()
        
        if last_booking:
            booking_animal = last_booking.bookinganimal_set.filter(animal=obj).first()
            return {
                'special_notes': booking_animal.special_notes if booking_animal else None,
                'last_booking_date': last_booking.end_date
            }
        return None

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price']

class BookingSerializer(serializers.ModelSerializer):
    # Поля из аннотаций
    booking_rating = serializers.IntegerField(read_only=True)
    has_review = serializers.BooleanField(read_only=True)
    review_length = serializers.IntegerField(read_only=True)
    review_date = serializers.DateTimeField(read_only=True)
    is_review_verified = serializers.BooleanField(read_only=True)
    days_until_review = serializers.DurationField(read_only=True)

    # Дополнительные вычисляемые поля
    review_status = serializers.SerializerMethodField()
    review_summary = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'dog_sitter', 'start_date', 'end_date',
            'status', 'total_price', 'booking_rating', 'has_review',
            'review_length', 'review_date', 'is_review_verified',
            'days_until_review', 'review_status', 'review_summary'
        ]

    def get_review_status(self, obj):
        """
        Возвращает статус отзыва
        """
        if not obj.has_review:
            return "Отзыв не оставлен"
        if obj.is_review_verified:
            return "Проверенный отзыв"
        return "Отзыв на проверке"

    def get_review_summary(self, obj):
        """
        Возвращает сводку по отзыву
        """
        if not obj.has_review:
            return None
        
        return {
            'rating': obj.booking_rating,
            'length': obj.review_length,
            'days_after_booking': obj.days_until_review.days if obj.days_until_review else None,
            'verified': obj.is_review_verified
        } 
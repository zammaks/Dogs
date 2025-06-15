from django.db.models import (
    Count, Avg, Sum, Min, Max, F, Q, 
    ExpressionWrapper, FloatField, IntegerField,
    Case, When, Value, CharField, BooleanField, DurationField
)
from django.db.models.functions import (
    ExtractMonth, ExtractYear, Concat, 
    Coalesce, Now, TruncDate, Extract, Length
)
from django.utils import timezone
from datetime import timedelta
from .models import Animal, Booking, DogSitter, Review, Service
from users.models import User

def get_dogsitter_statistics():
    """
    Получение статистики по догситтерам
    """
    return DogSitter.objects.annotate(
        total_bookings=Count('bookings'),
    
        active_bookings=Count('bookings', 
            filter=Q(bookings__status='confirmed') & 
                  Q(bookings__end_date__gte=timezone.now().date())
        ),
        
        avg_rating=Coalesce(
            Avg('bookings__review__rating'), 
            Value(0.0), 
            output_field=FloatField()
        ),
        
        # Общий заработок
        total_earnings=Coalesce(
            Sum('bookings__total_price', 
                filter=Q(bookings__status='completed')
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        
        # Количество постоянных клиентов (более 3 бронирований)
        regular_clients=Count(
            'bookings__user',
            filter=Q(bookings__status='completed'),
            distinct=True
        ),
        
        # Процент успешных бронирований
        success_rate=ExpressionWrapper(
            Case(
                When(total_bookings__gt=0,
                     then=Count('bookings', 
                          filter=Q(bookings__status='completed')
                     ) * 100.0 / F('total_bookings')),
                default=Value(0.0)
            ),
            output_field=FloatField()
        ),
        
        # Специализация (тип животных, с которыми чаще всего работает)
        main_pet_type=Coalesce(
            Case(
                When(
                    bookings__animals__type='dog',
                    then=Value('dog')
                ),
                When(
                    bookings__animals__type='cat',
                    then=Value('cat')
                ),
                default=Value('mixed'),
                output_field=CharField()
            ),
            Value('no_bookings')
        )
    )

def get_animal_statistics():
    """
    Получение статистики по животным с использованием аннотаций
    """
    return Animal.objects.annotate(
        # Количество завершенных бронирований
        completed_bookings=Count(
            'bookings',
            filter=Q(bookings__status='completed')
        ),
        
        # Средняя продолжительность бронирования
        avg_booking_duration=ExpressionWrapper(
            Avg(F('bookings__end_date') - F('bookings__start_date')),
            output_field=FloatField()
        ),
        
        # Любимый догситтер (самый частый)
        favorite_sitter=Case(
            When(bookings__isnull=False,
                 then=F('bookings__dog_sitter__user__first_name')),
            default=Value('Нет бронирований'),
            output_field=CharField()
        ),
        
        # Дней с последнего бронирования
        days_since_last_booking=ExpressionWrapper(
            Now() - Max('bookings__end_date'),
            output_field=IntegerField()
        ),
        
        # Общая стоимость всех услуг
        total_services_cost=Coalesce(
            Sum('bookings__total_price'),
            Value(0.0),
            output_field=FloatField()
        )
    )

def get_booking_analytics():
    """
    Аналитика по бронированиям с использованием аннотаций
    """
    current_date = timezone.now().date()
    return Booking.objects.annotate(
        # Продолжительность бронирования
        duration=ExpressionWrapper(
            F('end_date') - F('start_date'),
            output_field=IntegerField()
        ),
        
        # Количество животных в бронировании
        animals_count=Count('animals'),
        
        # Стоимость за день
        price_per_day=ExpressionWrapper(
            F('total_price') / F('duration'),
            output_field=FloatField()
        ),
        
        # Статус бронирования относительно текущей даты
        booking_status=Case(
            When(start_date__gt=current_date, 
                 then=Value('upcoming')),
            When(end_date__lt=current_date, 
                 then=Value('completed')),
            When(start_date__lte=current_date, end_date__gte=current_date,
                 then=Value('in_progress')),
            default=Value('unknown'),
            output_field=CharField()
        ),
        
        # Количество дополнительных услуг
        services_count=Count('services'),
        
        # Общая стоимость дополнительных услуг
        services_total_cost=Sum('services__price'),
        
        # Месяц бронирования
        booking_month=ExtractMonth('start_date'),
        
        # Год бронирования
        booking_year=ExtractYear('start_date')
    )

def get_user_statistics():
    """
    Статистика по пользователям с использованием аннотаций
    """
    return User.objects.annotate(
        # Количество животных у пользователя
        total_animals=Count('animals'),
        
        # Количество активных бронирований
        active_bookings=Count(
            'bookings',
            filter=Q(bookings__status='confirmed') & 
                  Q(bookings__end_date__gte=timezone.now().date())
        ),
        
        # Общая сумма потраченная на услуги
        total_spent=Coalesce(
            Sum('bookings__total_price', 
                filter=Q(bookings__status__in=['completed', 'confirmed'])
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        
        # Средняя оценка оставленных отзывов
        avg_review_rating=Avg('bookings__review__rating'),
        
        # Количество разных догситтеров, с которыми работал
        unique_dogsitters=Count(
            'bookings__dog_sitter',
            distinct=True
        ),
        
        # Предпочитаемый размер животных
        preferred_pet_size=Case(
            When(animals__size='small', then=Value('small')),
            When(animals__size='medium', then=Value('medium')),
            When(animals__size='large', then=Value('large')),
            default=Value('no_preference'),
            output_field=CharField()
        ),
        
        # Статус клиента
        client_status=Case(
            When(bookings__count__gt=10, then=Value('VIP')),
            When(bookings__count__gt=5, then=Value('Regular')),
            When(bookings__count__gt=0, then=Value('New')),
            default=Value('Inactive'),
            output_field=CharField()
        )
    )

def get_dogsitter_with_ratings():
    """
    Получение догситтеров с детальной информацией о рейтингах
    """
    return DogSitter.objects.annotate(
        # Средний рейтинг из всех отзывов
        average_rating=Coalesce(
            Avg('bookings__review__rating'),
            Value(0.0),
            output_field=FloatField()
        ),
        # Общее количество отзывов
        total_reviews=Count('bookings__review'),
        # Количество отзывов по каждой оценке
        five_star_reviews=Count(
            'bookings__review',
            filter=Q(bookings__review__rating=5)
        ),
        four_star_reviews=Count(
            'bookings__review',
            filter=Q(bookings__review__rating=4)
        ),
        three_star_reviews=Count(
            'bookings__review',
            filter=Q(bookings__review__rating=3)
        ),
        two_star_reviews=Count(
            'bookings__review',
            filter=Q(bookings__review__rating=2)
        ),
        one_star_reviews=Count(
            'bookings__review',
            filter=Q(bookings__review__rating=1)
        ),
        # Процент положительных отзывов (4 и 5 звезд)
        positive_reviews_percentage=ExpressionWrapper(
            Case(
                When(total_reviews__gt=0,
                     then=(F('five_star_reviews') + F('four_star_reviews')) * 100.0 / F('total_reviews')),
                default=Value(0.0)
            ),
            output_field=FloatField()
        ),
        # Количество отзывов за последний месяц
        recent_reviews=Count(
            'bookings__review',
            filter=Q(bookings__review__date__gte=timezone.now() - timedelta(days=30))
        )
    )

def get_bookings_with_ratings():
    """
    Получение бронирований с информацией о рейтингах и отзывах
    """
    return Booking.objects.annotate(
        # Рейтинг этого бронирования
        booking_rating=Coalesce(
            F('review__rating'),
            Value(0),
            output_field=IntegerField()
        ),
        # Наличие отзыва
        has_review=Case(
            When(review__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        ),
        # Длина отзыва в символах
        review_length=Length('review__comment'),
        # Дата отзыва
        review_date=F('review__date'),
        # Статус верификации отзыва
        is_review_verified=F('review__is_verified'),
        # Разница между датой завершения бронирования и датой отзыва (в днях)
        days_until_review=ExpressionWrapper(
            F('review__date') - F('end_date'),
            output_field=DurationField()
        )
    ) 
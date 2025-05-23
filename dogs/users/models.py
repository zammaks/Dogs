from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, fields, Avg, Count, Sum, Min, Max, Case, When, IntegerField, Q, Value, CharField
from django.db.models.functions import TruncMonth, TruncYear, Concat

def user_avatar_path(instance, filename):
    # Генерируем путь для сохранения аватарки: media/avatars/user_<id>/<filename>
    return f'avatars/user_{instance.id}/{filename}'

def user_photo_path(instance, filename):
    return f'photos/user_{instance.user.id}/{filename}'

class User(AbstractUser):
    """Модель для таблицы Users (Пользователи)"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отчество")
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        null=True,
        blank=True,
        verbose_name="Аватар"
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Телефон",
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Телефон должен быть в формате: '+79999999999'. Допускается до 15 цифр."
            )
        ]
    )
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")
    registration_date = models.DateTimeField(default=timezone.now, verbose_name="Дата регистрации")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return f"{self.last_name} {self.first_name}"
        
    def get_upcoming_bookings(self):
        today = timezone.now().date()
        return self.bookings.filter(start_date__gte=today).order_by('start_date')
        
    def get_booking_history(self, days=90):
        end_date = timezone.now().date() - timedelta(days=days)
        return self.bookings.filter(end_date__lte=timezone.now().date(), 
                                    end_date__gte=end_date).order_by('-end_date')

    def get_all_dogs(self):
        """Получение всех собак пользователя"""
        return self.animals.filter(type='dog')
    
    def get_all_cats(self):
        """Получение всех котов пользователя"""
        return self.animals.filter(type='cat')
    
    def get_active_bookings_count(self):
        """Получение количества активных бронирований пользователя"""
        return self.bookings.filter(
            status__in=['pending', 'confirmed']
        ).count()
        
    def get_animals_by_size(self, size):
        """Получает животных пользователя по размеру"""
        return self.animals.filter(size=size)
        
    def has_large_dogs(self):
        """Проверяет, есть ли у пользователя крупные собаки"""
        return self.animals.filter(
            type='dog', 
            size='large'
        ).exists()
        
    def get_bookings_with_dogsitter(self, dogsitter_id):
        return self.bookings.filter(dog_sitter__id=dogsitter_id)
        
    def get_bookings_with_service(self, service_name):
        return self.bookings.filter(services__name__icontains=service_name).distinct()
        
    def get_bookings_by_month(self, year, month):
        """Получает бронирования пользователя за указанный месяц и год"""
        return self.bookings.filter(
            start_date__year=year,
            start_date__month=month
        )
        
    def get_bookings_by_status_and_period(self, status, start_date, end_date):
        """Получает бронирования по статусу за определённый период"""
        return self.bookings.filter(
            status=status,
            start_date__gte=start_date,
            end_date__lte=end_date
        )
        
    def get_animals_without_bookings(self):
        """Получает животных пользователя, у которых нет бронирований"""
        return self.animals.filter(bookings__isnull=True)
        
    def get_most_recent_review(self):
        """Получает самый последний отзыв пользователя"""
        return self.bookings.filter(review__isnull=False).order_by('-review__date').first()
        
    def get_bookings_stats(self):
        return self.bookings.aggregate(
            total_bookings=Count('id'),
            total_animals=Count('animals', distinct=True),
            completed_bookings=Count('id', filter=Q(status='completed')),
            pending_bookings=Count('id', filter=Q(status='pending')),
            cancelled_bookings=Count('id', filter=Q(status='cancelled')),
            total_spent=Sum('total_price', filter=Q(status='completed')),
            avg_booking_price=Avg('total_price'),
            max_booking_price=Max('total_price'),
            min_booking_price=Min('total_price'),
            longest_booking=Max(F('end_date') - F('start_date')),
            shortest_booking=Min(F('end_date') - F('start_date')),
            avg_booking_duration=Avg(F('end_date') - F('start_date'))
        )
        
    def get_bookings_by_month_annotated(self):
        """
        Получает статистику бронирований по месяцам с использованием аннотирования
        """
        return self.bookings.annotate(
            month=TruncMonth('start_date'),
            year=TruncYear('start_date'),
            month_year=Concat(
                TruncMonth('start_date', output_field=CharField()),
                Value(' '),
                TruncYear('start_date', output_field=CharField()),
                output_field=CharField()
            )
        ).values('month_year', 'month').annotate(
            bookings_count=Count('id'),
            total_price=Sum('total_price'),
            avg_price=Avg('total_price'),
            animals_count=Count('animals', distinct=True)
        ).order_by('-month')
        
    def get_animals_with_bookings_stats(self):
        """
        Получает статистику по каждому животному с количеством бронирований
        """
        return self.animals.annotate(
            full_name=Concat(
                'name', Value(' ('), 'type', Value(')'),
                output_field=CharField()
            ),
            bookings_count=Count('bookings'),
            last_booking_date=Max('bookings__start_date'),
            total_services=Count('bookings__services', distinct=True),
            different_dogsitters=Count('bookings__dog_sitter', distinct=True),
            has_reviews=Case(
                When(bookings__review__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField()
            ),
            bookings_with_large_dogs=Count(
                'bookings',
                filter=Q(
                    bookings__animals__type='dog',
                    bookings__animals__size='large'
                ),
                distinct=True
            )
        ).order_by('-bookings_count')

    def get_absolute_url(self):
        return reverse('user_detail', args=[str(self.id)])
    
    def get_edit_url(self):
        return reverse('user_edit', args=[str(self.id)])
    
    def get_delete_url(self):
        return reverse('user_delete', args=[str(self.id)])

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['last_name', 'first_name']
        db_table = 'auth_user' 

class UserPhoto(models.Model):
    """Модель для хранения фотографий пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to=user_photo_path, verbose_name="Фотография")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    is_public = models.BooleanField(default=True, verbose_name="Публичное фото")

    class Meta:
        verbose_name = "Фотография пользователя"
        verbose_name_plural = "Фотографии пользователя"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Фото пользователя {self.user.get_full_name()} от {self.uploaded_at.strftime('%d.%m.%Y')}" 
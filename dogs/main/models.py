from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, fields, Avg, Count, Sum, Min, Max, Case, When, IntegerField, Q, Value, CharField
from django.urls import reverse
from django.db.models.functions import TruncMonth, TruncYear, Concat
from users.models import User
import os

def animal_photo_path(instance, filename):
    # Генерируем путь для сохранения фото животного: media/animals/user_id/animal_id/filename
    return os.path.join('animals', str(instance.user.id), str(instance.id), filename)

def dogsitter_document_path(instance, filename):
    # Генерируем путь для документов догситтера: media/dogsitters/user_id/filename
    return os.path.join('dogsitters', str(instance.user.id), filename)

def booking_document_path(instance, filename):
    # Генерируем путь для документов бронирования: media/bookings/booking_id/filename
    return os.path.join('bookings', str(instance.id), filename)

class BookingManager(models.Manager):
    
    def active(self):
        return self.filter(
            status__in=['pending', 'confirmed']
        ).select_related('user', 'dog_sitter').prefetch_related('animals', 'services').order_by('start_date')
    
    def pending(self):
        return self.filter(status='pending').select_related('user', 'dog_sitter').order_by('start_date')
    
    def confirmed(self):
        return self.filter(status='confirmed').select_related('user', 'dog_sitter').order_by('start_date')
    
    def completed(self):
        return self.filter(status='completed').select_related('user', 'dog_sitter').order_by('-end_date')
    
    def future(self):
        today = timezone.now().date()
        return self.filter(start_date__gt=today).order_by('start_date')
    
    def current(self):
        today = timezone.now().date()
        return self.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='confirmed'
        ).order_by('end_date')
    
    def with_large_dogs(self):
        return self.filter(
            animals__type='dog',
            animals__size='large'
        ).distinct()
    
    def long_term(self, min_days=7):
        """Возвращает долгосрочные бронирования"""
        duration = ExpressionWrapper(
            F('end_date') - F('start_date'), 
            output_field=fields.IntegerField()
        )
        return self.annotate(duration=duration).filter(duration__gte=min_days)

    def with_all_related(self):
        return self.select_related(
            'user', 
            'dog_sitter'
        ).prefetch_related(
            'animals',
            'services',
            'animals__user', 
            'bookinganimal_set' 
        )


class Animal(models.Model):
    """Модель для таблицы Animals (Животные)"""
    DOG = 'dog'
    CAT = 'cat'
    OTHER = 'other'
    
    ANIMAL_TYPE_CHOICES = [
        (DOG, 'Собака'),
        (CAT, 'Кошка'),
        (OTHER, 'Другое'),
    ]
    
    SIZE_SMALL = 'small'
    SIZE_MEDIUM = 'medium'
    SIZE_LARGE = 'large'
    
    ANIMAL_SIZE_CHOICES = [
        (SIZE_SMALL, 'Маленький'),
        (SIZE_MEDIUM, 'Средний'),
        (SIZE_LARGE, 'Большой'),
    ]
    
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=ANIMAL_TYPE_CHOICES)
    breed = models.CharField(max_length=50, blank=True)
    age = models.IntegerField()
    size = models.CharField(max_length=10, choices=ANIMAL_SIZE_CHOICES)
    special_needs = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='animals')
    is_available = models.BooleanField(default=True, verbose_name="Доступен")
    photo = models.FileField(
        upload_to=animal_photo_path,
        null=True,
        blank=True,
        verbose_name="Фотография животного"
    )

    def __str__(self):
        return self.name
        
    def get_size_display_verbose(self):
        """Расширенное описание размера животного с дополнительной информацией"""
        size_descriptions = {
            self.SIZE_SMALL: "Маленький (до 10 кг)",
            self.SIZE_MEDIUM: "Средний (10-25 кг)",
            self.SIZE_LARGE: "Крупный (более 25 кг)"
        }
        return size_descriptions.get(self.size, "Неизвестный размер")

    def has_current_booking(self):
        today = timezone.now().date()
        return self.bookings.filter(
            start_date__lte=today,
            end_date__gte=today,
            status=Booking.STATUS_CONFIRMED
        ).exists()
    
    def get_last_booking(self):
        return self.bookings.order_by('-start_date').first()
        
    def get_bookings_by_period(self, start_date, end_date):
        return self.bookings.filter(
            start_date__gte=start_date,
            end_date__lte=end_date
        )
        
    def get_bookings_with_specific_dogsitter(self, dogsitter_name):
        return self.bookings.filter(
            dog_sitter__first_name__icontains=dogsitter_name
        ).distinct()
        
    def get_future_bookings_count(self):
        today = timezone.now().date()
        return self.bookings.filter(
            start_date__gt=today
        ).count()
        
    def has_bookings_with_review(self):
        return self.bookings.filter(
            review__isnull=False
        ).exists()
        
    def has_been_with_dogsitter(self, dogsitter_id):
        return self.bookings.filter(
            dog_sitter__id=dogsitter_id
        ).exists()

    def get_absolute_url(self):
        """
        Возвращает URL для просмотра детальной информации о животном
        """
        return reverse('animal_detail', args=[str(self.id)])
    
    def get_edit_url(self):
        """
        Возвращает URL для редактирования животного
        """
        return reverse('animal_edit', args=[str(self.id)])
    
    def get_owner_url(self):
        """
        Возвращает URL для просмотра профиля владельца животного
        """
        return reverse('user_detail', args=[str(self.user.id)])

    @classmethod
    def get_all_with_owners(cls):
        """Получает всех животных с информацией о владельцах"""
        return cls.objects.select_related('user').all()
    
    def get_bookings_with_details(self):
        """Получает все бронирования животного с полной информацией"""
        return self.bookings.select_related('dog_sitter', 'user').prefetch_related('services').all()

    @classmethod
    def get_with_bookings_and_reviews(cls):
        """Получает животных с их бронированиями и отзывами"""
        return cls.objects.prefetch_related(
            'bookings',
            'bookings__review',
            'bookings__services'
        ).select_related('user')

    class Meta:
        verbose_name = "Животное"
        verbose_name_plural = "Животные"
        ordering = ['name']


class Service(models.Model):
    """Модель для таблицы Services (Услуги)"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ['price', 'name']


class DogSitter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.FloatField(default=0.0)
    description = models.TextField(blank=True)
    experience_years = models.IntegerField(default=0)
    last_login = models.DateTimeField(default=timezone.now)
    avatar = models.FileField(
        upload_to=dogsitter_document_path,
        null=True,
        blank=True,
        verbose_name="Фотография профиля"
    )
    passport_scan = models.FileField(
        upload_to=dogsitter_document_path,
        null=True,
        blank=True,
        verbose_name="Скан паспорта"
    )
    medical_certificate = models.FileField(
        upload_to=dogsitter_document_path,
        null=True,
        blank=True,
        verbose_name="Медицинская справка"
    )
    experience_certificate = models.FileField(
        upload_to=dogsitter_document_path,
        null=True,
        blank=True,
        verbose_name="Сертификат о квалификации"
    )
    website = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Личный сайт"
    )
    social_media_links = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Ссылки на соцсети"
    )

    def __str__(self):
        return f"Догситтер {self.user.last_name} {self.user.first_name}"
        
    def update_last_login(self):
        """Обновление времени последнего входа"""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
        
    def is_active(self):
        """Проверяет, был ли догситтер активен в последние 30 дней"""
        if not self.last_login:
            return False
        return self.last_login >= (timezone.now() - timedelta(days=30))

    def calculate_total_earnings(self):
        """Расчет общего заработка догситтера"""
        completed_bookings = self.bookings.filter(status=Booking.STATUS_COMPLETED)
        return sum(booking.total_price for booking in completed_bookings if booking.total_price)
    
    def get_average_rating_from_reviews(self):
        """Получение среднего рейтинга из всех отзывов по бронированиям догситтера"""
        reviews = Review.objects.filter(booking__dog_sitter=self)
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / reviews.count()
        
    def get_bookings_by_animal_type(self, animal_type):
        """Получает бронирования догситтера с животными указанного типа"""
        return self.bookings.filter(
            animals__type=animal_type
        ).distinct()
        
    def get_bookings_with_large_animals(self):
        """Получает бронирования догситтера с крупными животными"""
        return self.bookings.filter(
            animals__size=Animal.SIZE_LARGE
        ).distinct()
        
    def get_bookings_by_status(self, status):
        """Получает бронирования догситтера по статусу"""
        return self.bookings.filter(status=status)
        
    def get_clients_with_large_dogs(self):
        """Получает список клиентов догситтера с крупными собаками"""
        return User.objects.filter(
            bookings__dog_sitter=self,
            bookings__animals__type=Animal.DOG,
            bookings__animals__size=Animal.SIZE_LARGE
        ).distinct()
        
    def get_future_bookings(self):
        return Booking.objects.future().filter(dog_sitter=self)
        
    def get_active_bookings(self):
        return Booking.objects.active().filter(dog_sitter=self)
        
    def get_completed_bookings(self):
        return Booking.objects.completed().filter(dog_sitter=self)
        
    def count_bookings_by_month(self, year, month):
        """Подсчитывает количество бронирований за указанный месяц"""
        return self.bookings.filter(
            start_date__year=year,
            start_date__month=month
        ).count()
        
    def get_statistics(self):
        """Получает статистику по догситтеру"""
        # Получаем статистику по бронированиям
        bookings_stats = self.bookings.aggregate(
            total_bookings=Count('id'),
            completed_bookings=Count('id', filter=Q(status=Booking.STATUS_COMPLETED)),
            cancelled_bookings=Count('id', filter=Q(status=Booking.STATUS_CANCELLED)),
            total_earnings=Sum('total_price', filter=Q(status=Booking.STATUS_COMPLETED)),
            avg_booking_price=Avg('total_price')
        )
        
        # Получаем среднюю продолжительность бронирований отдельно
        duration_stats = self.bookings.annotate(
            duration=ExpressionWrapper(
                F('end_date') - F('start_date'),
                output_field=fields.DurationField()
            )
        ).aggregate(
            avg_booking_duration=Avg('duration')
        )
        
        # Обрабатываем None значения в статистике бронирований
        bookings_stats['total_bookings'] = bookings_stats.get('total_bookings', 0)
        bookings_stats['completed_bookings'] = bookings_stats.get('completed_bookings', 0)
        bookings_stats['cancelled_bookings'] = bookings_stats.get('cancelled_bookings', 0)
        bookings_stats['total_earnings'] = float(bookings_stats.get('total_earnings', 0) or 0)
        bookings_stats['avg_booking_price'] = float(bookings_stats.get('avg_booking_price', 0) or 0)
        
        # Преобразуем timedelta в дни
        avg_duration = duration_stats.get('avg_booking_duration')
        bookings_stats['avg_booking_duration'] = avg_duration.days if avg_duration else 0
        
        # Получаем статистику по животным
        animals_stats = self.bookings.aggregate(
            total_animals=Count('animals', distinct=True),
            dogs_count=Count('animals', filter=Q(animals__type=Animal.DOG), distinct=True),
            cats_count=Count('animals', filter=Q(animals__type=Animal.CAT), distinct=True),
            small_animals=Count('animals', filter=Q(animals__size=Animal.SIZE_SMALL), distinct=True),
            medium_animals=Count('animals', filter=Q(animals__size=Animal.SIZE_MEDIUM), distinct=True),
            large_animals=Count('animals', filter=Q(animals__size=Animal.SIZE_LARGE), distinct=True)
        )
        
        # Обрабатываем None значения в статистике животных
        for key in animals_stats:
            animals_stats[key] = animals_stats.get(key, 0)
        
        # Получаем статистику по отзывам
        reviews_stats = Review.objects.filter(booking__dog_sitter=self).aggregate(
            total_reviews=Count('id'),
            avg_rating=Avg('rating'),
            five_star_reviews=Count('id', filter=Q(rating=5)),
            four_star_reviews=Count('id', filter=Q(rating=4)),
            three_star_reviews=Count('id', filter=Q(rating=3)),
            two_star_reviews=Count('id', filter=Q(rating=2)),
            one_star_reviews=Count('id', filter=Q(rating=1))
        )
        
        reviews_stats['total_reviews'] = reviews_stats.get('total_reviews', 0)
        reviews_stats['avg_rating'] = float(reviews_stats.get('avg_rating', 0) or 0)
        reviews_stats['five_star_reviews'] = reviews_stats.get('five_star_reviews', 0)
        reviews_stats['four_star_reviews'] = reviews_stats.get('four_star_reviews', 0)
        reviews_stats['three_star_reviews'] = reviews_stats.get('three_star_reviews', 0)
        reviews_stats['two_star_reviews'] = reviews_stats.get('two_star_reviews', 0)
        reviews_stats['one_star_reviews'] = reviews_stats.get('one_star_reviews', 0)

        return {
            'bookings_stats': bookings_stats,
            'animals_stats': animals_stats,
            'reviews_stats': reviews_stats
        }
        
    def get_bookings_by_month(self):
        return self.bookings.annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            count=Count('id'),
            total_revenue=Sum('total_price'),
            avg_price=Avg('total_price')
        ).order_by('-month')
        
    def get_clients_with_stats(self):
        return User.objects.filter(
            bookings__dog_sitter=self
        ).annotate(
            full_name=Concat('last_name', Value(' '), 'first_name', output_field=CharField()),
            booking_count=Count('bookings', filter=Q(bookings__dog_sitter=self)),
            last_booking=Max('bookings__start_date', filter=Q(bookings__dog_sitter=self)),
            total_spent=Sum('bookings__total_price', filter=Q(
                bookings__dog_sitter=self,
                bookings__status=Booking.STATUS_COMPLETED
            )),
            animals_count=Count('animals', distinct=True),
            has_reviewed=Case(
                When(bookings__review__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField()
            ),
            avg_rating=Avg('bookings__review__rating', filter=Q(bookings__dog_sitter=self))
        ).order_by('-booking_count')

    def get_absolute_url(self):
        """
        Возвращает URL для просмотра детальной информации о догситтере
        """
        return reverse('dogsitter_detail', args=[str(self.id)])
    
    def get_edit_url(self):
        """
        Возвращает URL для редактирования профиля догситтера
        """
        return reverse('dogsitter_edit', args=[str(self.id)])
    
    def get_bookings_url(self):
        """
        Возвращает URL для просмотра всех бронирований догситтера
        """
        return reverse('dogsitter_bookings', args=[str(self.id)])
    
    def get_reviews_url(self):
        """
        Возвращает URL для просмотра всех отзывов о догситтере
        """
        return reverse('dogsitter_reviews', args=[str(self.id)])

    @classmethod
    def get_all_with_users(cls):
        """Получает всех догситтеров с информацией о пользователях"""
        return cls.objects.select_related('user').all()
    
    def get_active_bookings_with_details(self):
        """Получает активные бронирования с полной информацией"""
        return self.bookings.filter(
            status__in=['pending', 'confirmed']
        ).select_related('user').prefetch_related('animals', 'services')

    @classmethod
    def get_with_full_history(cls):
        """Получает догситтеров с полной историей бронирований и отзывов"""
        return cls.objects.select_related('user').prefetch_related(
            'bookings',
            'bookings__animals',
            'bookings__services',
            'bookings__review'
        )

    def get_bookings_with_animals_and_reviews(self):
        """Получает бронирования догситтера с животными и отзывами"""
        return self.bookings.select_related('user').prefetch_related(
            'animals',
            'services',
            'review',
            'bookinganimal_set'  # Для доступа к дополнительной информации о животных
        )

    def delete(self, *args, **kwargs):
        # Удаляем файлы при удалении объекта
        if self.passport_scan:
            if os.path.isfile(self.passport_scan.path):
                os.remove(self.passport_scan.path)
        if self.medical_certificate:
            if os.path.isfile(self.medical_certificate.path):
                os.remove(self.medical_certificate.path)
        if self.experience_certificate:
            if os.path.isfile(self.experience_certificate.path):
                os.remove(self.experience_certificate.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Догситтер"
        verbose_name_plural = "Догситтеры"
        ordering = ['-rating', 'user__last_name']


class BookingAnimal(models.Model):
    """Промежуточная модель для связи Booking и Animal"""
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, verbose_name="Бронирование")
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, verbose_name="Животное")
    special_notes = models.TextField(blank=True, verbose_name="Особые заметки")
    special_diet = models.CharField(max_length=255, blank=True, verbose_name="Особая диета")
    medications = models.TextField(blank=True, verbose_name="Медикаменты")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Время добавления")
    
    def __str__(self):
        return f"{self.animal.name} в бронировании {self.booking.id}"
    
    @classmethod
    def get_all_with_details(cls):
        """Получает все записи о животных в бронированиях с полной информацией"""
        return cls.objects.select_related(
            'booking',
            'animal',
            'booking__user',
            'booking__dog_sitter',
            'animal__user'
        ).prefetch_related(
            'booking__services'
        )

    class Meta:
        verbose_name = "Животное в бронировании"
        verbose_name_plural = "Животные в бронировании"
        unique_together = ['booking', 'animal']


class Booking(models.Model):
    """Модель для таблицы Booking (Бронирования)"""
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает подтверждения"),
        (STATUS_CONFIRMED, "Подтверждено"),
        (STATUS_COMPLETED, "Завершено"),
        (STATUS_CANCELLED, "Отменено")
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings", verbose_name="Владелец")
    animals = models.ManyToManyField(
        Animal,
        through='BookingAnimal',
        related_name="bookings",
        verbose_name="Животные"
    )
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    services = models.ManyToManyField(Service, related_name="bookings", verbose_name="Услуги")
    dog_sitter = models.ForeignKey(DogSitter, on_delete=models.CASCADE, related_name="bookings", verbose_name="Догситтер")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="Статус бронирования"
    )
    contract_file = models.FileField(
        upload_to=booking_document_path,
        null=True,
        blank=True,
        verbose_name="Договор"
    )
    payment_receipt = models.FileField(
        upload_to=booking_document_path,
        null=True,
        blank=True,
        verbose_name="Чек об оплате"
    )
    additional_documents = models.FileField(
        upload_to=booking_document_path,
        null=True,
        blank=True,
        verbose_name="Дополнительные документы"
    )
    
    objects = BookingManager()

    def save(self, *args, **kwargs):
        # Сохраняем объект, чтобы получить id (если это новый объект)
        if not self.pk:
            super().save(*args, **kwargs)

        # Проверка, что даты не в прошлом
        if self.start_date < timezone.now().date():
            raise ValueError("Дата начала бронирования не может быть в прошлом.")

        # Рассчитываем стоимость
        days = (self.end_date - self.start_date).days
        if days < 0:
            raise ValueError("Дата окончания бронирования должна быть позже даты начала.")

        # Стоимость услуг
        service_cost = sum(service.price for service in self.services.all())

        # Стоимость животных (в зависимости от размера)
        size_cost_map = {"Маленький": 500, "Средний": 700, "Крупный": 1000}
        animal_cost = sum(size_cost_map.get(animal.size, 500) for animal in self.animals.all())

        # Общая стоимость
        self.total_price = (service_cost + animal_cost) * days

        # Сохраняем объект с обновленной стоимостью
        super().save(*args, **kwargs)

    def is_active(self):
        """Проверяет, является ли бронирование активным"""
        return self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED]
        
    def can_be_cancelled(self):
        """Проверяет, можно ли отменить бронирование"""
        return self.status != self.STATUS_COMPLETED and self.start_date > timezone.now().date()
        
    def get_duration_days(self):
        """Получает продолжительность бронирования в днях"""
        return (self.end_date - self.start_date).days
        
    def includes_cat(self):
        """Проверяет, включает ли бронирование кошек"""
        return self.animals.filter(type=Animal.CAT).exists()
        
    def includes_large_dog(self):
        """Проверяет, включает ли бронирование крупных собак"""
        return self.animals.filter(
            type=Animal.DOG,
            size=Animal.SIZE_LARGE
        ).exists()
        
    def has_animals_with_special_needs(self):
        return self.animals.filter(
            special_needs__isnull=False
        ).exclude(special_needs__exact='').exists()
        
    def is_long_term(self):
        """Проверяет, является ли бронирование долгосрочным (более 7 дней)"""
        return self.get_duration_days() > 7
        
    def was_created_recently(self):
        """Проверяет, было ли бронирование создано недавно (в течение последних 24 часов)"""
        return self.created_at >= (timezone.now() - timedelta(days=1))
        
    def calculate_cost_per_day(self):
        """Рассчитывает стоимость бронирования за день"""
        days = self.get_duration_days()
        if days <= 0 or not self.total_price:
            return 0
        return self.total_price / days
        
    def __str__(self):
        return f"Бронирование для {self.user.last_name} {self.user.first_name} с {self.start_date} по {self.end_date}"

    def get_absolute_url(self):
        """
        Возвращает URL для просмотра детальной информации о бронировании
        """
        return reverse('booking_detail', args=[str(self.id)])
    
    def get_edit_url(self):
        """
        Возвращает URL для редактирования бронирования
        """
        return reverse('booking_edit', args=[str(self.id)])
    
    def get_cancel_url(self):
        """
        Возвращает URL для отмены бронирования
        """
        return reverse('booking_cancel', args=[str(self.id)])
    
    def get_complete_url(self):
        """
        Возвращает URL для завершения бронирования
        """
        return reverse('booking_complete', args=[str(self.id)])
    
    def get_user_url(self):
        """
        Возвращает URL для просмотра профиля пользователя
        """
        return reverse('user_detail', args=[str(self.user.id)])
    
    def get_dogsitter_url(self):
        """
        Возвращает URL для просмотра профиля догситтера
        """
        return reverse('dogsitter_detail', args=[str(self.dog_sitter.id)])

    @classmethod
    def get_active_with_all_details(cls):
        """Получает активные бронирования со всеми связанными данными"""
        return cls.objects.filter(
            status__in=[cls.STATUS_PENDING, cls.STATUS_CONFIRMED]
        ).select_related(
            'user',
            'dog_sitter'
        ).prefetch_related(
            'animals',
            'services',
            'bookinganimal_set',
            'review'
        )

    def get_animals_with_details(self):
        """Получает животных в бронировании с дополнительной информацией"""
        return self.animals.select_related('user').prefetch_related(
            'bookinganimal_set'
        )

    def delete(self, *args, **kwargs):
        # Удаляем файлы при удалении объекта
        if self.contract_file:
            if os.path.isfile(self.contract_file.path):
                os.remove(self.contract_file.path)
        if self.payment_receipt:
            if os.path.isfile(self.payment_receipt.path):
                os.remove(self.payment_receipt.path)
        if self.additional_documents:
            if os.path.isfile(self.additional_documents.path):
                os.remove(self.additional_documents.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-start_date']

class Review(models.Model):
    """Модель для таблицы Reviews (Отзывы)"""
    # Константы для оценок
    RATING_CHOICES = [
        (1, "⭐ Очень плохо"),
        (2, "⭐⭐ Плохо"),
        (3, "⭐⭐⭐ Нормально"),
        (4, "⭐⭐⭐⭐ Хорошо"),
        (5, "⭐⭐⭐⭐⭐ Отлично")
    ]
    
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name="review", 
        verbose_name="Бронирование"
    )
    rating = models.IntegerField(
        verbose_name="Оценка", 
        choices=RATING_CHOICES,
        default=5
    )
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    date = models.DateTimeField(default=timezone.now, verbose_name="Дата отзыва")
    is_verified = models.BooleanField(default=False, verbose_name="Проверен")

    def save(self, *args, **kwargs):
        """Обновление рейтинга догситтера после отзыва"""
        super().save(*args, **kwargs)
        if self.booking.dog_sitter:
            sitter = self.booking.dog_sitter
            all_ratings = [review.rating for review in Review.objects.filter(booking__dog_sitter=sitter)]
            sitter.rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
            sitter.save()
            
    def is_recent_review(self):
        """Проверяет, является ли отзыв недавним (создан менее 7 дней назад)"""
        return self.date >= (timezone.now() - timedelta(days=7))
        
    def get_rating_stars(self):
        """Возвращает строку со звездами для отображения оценки"""
        return "⭐" * self.rating
        
    def was_for_large_dog(self):
        """Проверяет, был ли отзыв на бронирование с крупными собаками"""
        return self.booking.animals.filter(
            type=Animal.DOG,
            size=Animal.SIZE_LARGE
        ).exists()
        
    def was_for_cat(self):
        """Проверяет, был ли отзыв на бронирование с кошками"""
        return self.booking.animals.filter(
            type=Animal.CAT
        ).exists()
        
    def was_for_long_booking(self):
        """Проверяет, был ли отзыв на долгосрочное бронирование (более 7 дней)"""
        return (self.booking.end_date - self.booking.start_date).days > 7
        
    def __str__(self):
        return f"Отзыв на бронирование {self.booking.id}"

    def get_absolute_url(self):
        """
        Возвращает URL для просмотра детальной информации об отзыве
        """
        return reverse('review_detail', args=[str(self.id)])
    
    def get_edit_url(self):
        """
        Возвращает URL для редактирования отзыва
        """
        return reverse('review_edit', args=[str(self.id)])
    
    def get_booking_url(self):
        """
        Возвращает URL для просмотра бронирования, к которому относится отзыв
        """
        return reverse('booking_detail', args=[str(self.booking.id)])
    
    def get_dogsitter_url(self):
        """
        Возвращает URL для просмотра профиля догситтера, которому оставлен отзыв
        """
        return reverse('dogsitter_detail', args=[str(self.booking.dog_sitter.id)])

    @classmethod
    def get_recent_with_details(cls):
        """Получает недавние отзывы со всей связанной информацией"""
        return cls.objects.select_related(
            'booking', 
            'booking__user', 
            'booking__dog_sitter'
        ).order_by('-date')[:10]

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-date']



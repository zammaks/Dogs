from django.db import models
from django.utils import timezone
from users.models import User

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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Животное"
        verbose_name_plural = "Животные"
        ordering = ['name']

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
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="Статус бронирования"
    )

    def __str__(self):
        return f"Бронирование {self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-start_date']

class BookingAnimal(models.Model):
    """Промежуточная модель для связи Booking и Animal"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, verbose_name="Бронирование")
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, verbose_name="Животное")
    special_notes = models.TextField(blank=True, verbose_name="Особые заметки")
    special_diet = models.CharField(max_length=255, blank=True, verbose_name="Особая диета")
    medications = models.TextField(blank=True, verbose_name="Медикаменты")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Время добавления")
    
    def __str__(self):
        return f"{self.animal.name} в бронировании {self.booking.id}"
    
    class Meta:
        verbose_name = "Животное в бронировании"
        verbose_name_plural = "Животные в бронировании"
        unique_together = ['booking', 'animal']

Booking.animals = models.ManyToManyField(
    Animal,
    through='BookingAnimal',
    related_name="bookings",
    verbose_name="Животные"
) 
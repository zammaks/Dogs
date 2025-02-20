from django.db import models

class User(models.Model):
    """Модель для таблицы Users (Пользователи)"""
    name = models.CharField(max_length=100, verbose_name="Имя")
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Телефон")
    role = models.CharField(max_length=50, verbose_name="Роль")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Animal(models.Model):
    """Модель для таблицы Animals (Животные)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="animals", verbose_name="Владелец")
    name = models.CharField(max_length=100, verbose_name="Кличка")
    type = models.CharField(max_length=50, verbose_name="Вид")
    breed = models.CharField(max_length=100, blank=True, null=True, verbose_name="Порода")
    age = models.IntegerField(blank=True, null=True, verbose_name="Возраст")
    special_needs = models.TextField(blank=True, null=True, verbose_name="Особые потребности")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Животное"
        verbose_name_plural = "Животные"

class Service(models.Model):
    """Модель для таблицы Services (Услуги)"""
    boarding = models.ForeignKey('Boarding', on_delete=models.CASCADE, related_name="services_set", verbose_name="Передержка")
    name = models.CharField(max_length=100, verbose_name="Название услуги")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Boarding(models.Model):
    """Модель для таблицы Boarding (Передержки)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boardings", verbose_name="Передержка")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за день")
    capacity = models.IntegerField(verbose_name="Вместимость")
    services = models.ManyToManyField(Service, related_name="boardings", verbose_name="Услуги")  # ManyToManyField

    def __str__(self):
        return f"Передержка {self.user.name}"

    class Meta:
        verbose_name = "Передержка"
        verbose_name_plural = "Передержки"


class Order(models.Model):
    """Модель для таблицы Orders (Заказы)"""
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="orders", verbose_name="Животное")
    boarding = models.ForeignKey(Boarding, on_delete=models.CASCADE, related_name="orders", verbose_name="Передержка")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость")

    def __str__(self):
        return f"Заказ {self.animal.name} в {self.boarding.user.name}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class Review(models.Model):
    """Модель для таблицы Reviews (Отзывы)"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="review", verbose_name="Заказ")
    rating = models.IntegerField(verbose_name="Оценка", choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    date = models.DateField(auto_now_add=True, verbose_name="Дата отзыва")

    def __str__(self):
        return f"Отзыв на заказ {self.order.id}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"



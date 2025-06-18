from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect, Http404, HttpRequest, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Count, Avg, Sum, F, ExpressionWrapper, fields, QuerySet
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncMonth, Concat
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from typing import Dict, List, Optional, Any

from .models import User, Animal, Booking, DogSitter, Service, Review


def index(request: HttpRequest) -> HttpResponse:
    """
    Отображение главной страницы сайта.

    Args:
        request: Объект HTTP-запроса

    Returns:
        HttpResponse: Отрендеренная главная страница с контекстными данными
    """
    animals_count = Animal.objects.count()
    bookings_count = Booking.objects.count()
    dogsitters_count = DogSitter.objects.count()
    
    top_dogsitters = DogSitter.objects.order_by('-rating')[:5]
    
    context = {
        'animals_count': animals_count,
        'bookings_count': bookings_count,
        'dogsitters_count': dogsitters_count,
        'top_dogsitters': top_dogsitters,
    }
    return render(request, 'main/index.html', context)


def search_dogsitters(request: HttpRequest) -> HttpResponse:
    """
    Поиск догситтеров с возможностью фильтрации по различным параметрам.

    Args:
        request: Объект HTTP-запроса с параметрами фильтрации
            - min_rating: минимальный рейтинг догситтера
            - has_reviews: наличие отзывов
            - active_only: только активные догситтеры

    Returns:
        HttpResponse: Отрендеренная страница со списком отфильтрованных догситтеров
    """
    min_rating = request.GET.get('min_rating', 0)
    
    dogsitters: QuerySet[DogSitter] = DogSitter.objects.all()
    
    if min_rating:
        dogsitters = dogsitters.filter(rating__gte=float(min_rating))
    
    if 'has_reviews' in request.GET:
        dogsitters = dogsitters.annotate(review_count=Count('bookings__review')).filter(review_count__gt=0)
    
    if 'active_only' in request.GET:
        active_date = timezone.now() - timezone.timedelta(days=30)
        dogsitters = dogsitters.filter(last_login__gte=active_date)
    
    dogsitters = dogsitters.order_by('-rating')
    
    context = {
        'dogsitters': dogsitters,
        'min_rating': min_rating,
    }
    return render(request, 'main/dogsitters_list.html', context)


class AnimalListView(ListView):
    """
    Представление для отображения списка животных с возможностью фильтрации.
    
    Attributes:
        model: Модель Animal для работы со списком животных
        template_name: Путь к шаблону для отображения списка
        context_object_name: Имя переменной контекста для списка животных
        paginate_by: Количество животных на одной странице
    """
    model = Animal
    template_name = 'main/animal_list.html'
    context_object_name = 'animals'
    paginate_by = 10
    
    def get_queryset(self) -> QuerySet[Animal]:
        """
        Получение отфильтрованного списка животных.

        Returns:
            QuerySet[Animal]: Отфильтрованный список животных
        """
        queryset = super().get_queryset()
        
        animal_type = self.request.GET.get('type')
        animal_size = self.request.GET.get('size')
        
        if animal_type:
            queryset = queryset.filter(type=animal_type)
        
        if animal_size:
            queryset = queryset.filter(size=animal_size)
            
        user_id = self.request.GET.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(breed__icontains=search_query)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Добавление дополнительных данных в контекст шаблона.

        Returns:
            Dict[str, Any]: Расширенный контекст шаблона
        """
        context = super().get_context_data(**kwargs)
        context['animal_types'] = Animal.ANIMAL_TYPE_CHOICES
        context['animal_sizes'] = Animal.ANIMAL_SIZE_CHOICES
        
        context['current_type'] = self.request.GET.get('type', '')
        context['current_size'] = self.request.GET.get('size', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


def booking_list(request: HttpRequest) -> HttpResponse:
    """
    Отображение списка бронирований с возможностью фильтрации по различным параметрам.

    Args:
        request: Объект HTTP-запроса с параметрами фильтрации
            - status: статус бронирования
            - start_date: дата начала периода
            - end_date: дата окончания периода
            - user_id: ID пользователя
            - dogsitter_id: ID догситтера
            - service_id: ID услуги
            - animal_type: тип животного
            - has_review: наличие отзыва
            - sort: поле для сортировки

    Returns:
        HttpResponse: Отрендеренная страница со списком отфильтрованных бронирований
    """
    bookings = Booking.objects.all()
    
    status = request.GET.get('status')
    if status:
        bookings = bookings.filter(status=status)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        bookings = bookings.filter(start_date__gte=start_date)
    
    if end_date:
        bookings = bookings.filter(end_date__lte=end_date)
    
    user_id = request.GET.get('user_id')
    if user_id:
        bookings = bookings.filter(user_id=user_id)
    
    # Фильтрация по догситтеру
    dogsitter_id = request.GET.get('dogsitter_id')
    if dogsitter_id:
        bookings = bookings.filter(dog_sitter_id=dogsitter_id)
    
    # Фильтрация по включенным услугам (связь ManyToMany)
    service_id = request.GET.get('service_id')
    if service_id:
        bookings = bookings.filter(services__id=service_id)
    
    # Фильтрация по типу животных в бронировании (сложная связь)
    animal_type = request.GET.get('animal_type')
    if animal_type:
        bookings = bookings.filter(animals__type=animal_type).distinct()
    
    # Фильтрация по наличию отзыва
    has_review = request.GET.get('has_review')
    if has_review:
        if has_review == 'yes':
            # Бронирования с отзывами (используем related_name="review")
            bookings = bookings.filter(review__isnull=False)
        elif has_review == 'no':
            # Бронирования без отзывов
            bookings = bookings.filter(review__isnull=True)
    
    # Сортировка результатов
    sort_by = request.GET.get('sort', '-start_date')  # По умолчанию сортируем по дате начала (убывание)
    bookings = bookings.order_by(sort_by)
    
    context = {
        'bookings': bookings,
        'statuses': Booking.STATUS_CHOICES,
        # Добавляем другие контекстные данные для фильтров и сортировки
    }
    
    return render(request, 'main/booking_list.html', context)


def api_animal_search(request: HttpRequest) -> JsonResponse:
    """
    API-представление для поиска животных с фильтрацией.

    Args:
        request: Объект HTTP-запроса с параметрами поиска
            - query: строка поиска по имени или породе
            - type: тип животного

    Returns:
        JsonResponse: JSON-ответ со списком найденных животных
    """
    query = request.GET.get('query', '')
    animal_type = request.GET.get('type', '')
    
    animals: QuerySet[Animal] = Animal.objects.all()
    
    if query:
        animals = animals.filter(
            Q(name__icontains=query) | 
            Q(breed__icontains=query)
        )
    
    if animal_type:
        animals = animals.filter(type=animal_type)
    
    animals_data = [
        {
            'id': animal.id,
            'name': animal.name,
            'type': animal.get_type_display(),
            'breed': animal.breed,
            'owner': f"{animal.user.first_name} {animal.user.last_name}",
        }
        for animal in animals[:20] 
    ]
    
    return JsonResponse({'results': animals_data})


def advanced_filter_examples(request: HttpRequest) -> HttpResponse:
    """
    Примеры различных типов фильтрации в Django ORM.

    Args:
        request: Объект HTTP-запроса

    Returns:
        HttpResponse: Отрендеренная страница с результатами фильтрации
    """

    expensive_bookings: QuerySet[Booking] = Booking.objects.filter(total_price__gt=5000)
    

    terrier_dogs: QuerySet[Animal] = Animal.objects.filter(breed__contains="терьер")
    
    # Фильтрация по началу строки
    i_users: QuerySet[User] = User.objects.filter(last_name__startswith="И")
    
    # Фильтрация по дате
    week_ago = timezone.now().date() - timedelta(days=7)
    recent_bookings: QuerySet[Booking] = Booking.objects.filter(start_date__gte=week_ago)
    
    # Поиск по диапазону значений
    middle_age_animals: QuerySet[Animal] = Animal.objects.filter(age__range=(3, 8))
    
    # Поиск по списку значений
    specific_sizes: QuerySet[Animal] = Animal.objects.filter(
        size__in=[Animal.SIZE_SMALL, Animal.SIZE_LARGE]
    )
    
    # Исключение значений
    not_cats: QuerySet[Animal] = Animal.objects.exclude(type=Animal.CAT)
    
    # Проверка на NULL / NOT NULL
    animals_with_breed: QuerySet[Animal] = Animal.objects.filter(breed__isnull=False)
    
    # Простая связь ForeignKey
    user_animals: QuerySet[Animal] = Animal.objects.filter(user__id=1)
    
    # Фильтрация по полям связанной модели
    ivanov_animals: QuerySet[Animal] = Animal.objects.filter(user__last_name="Иванов")

    context = {
        'expensive_bookings': expensive_bookings,
        'terrier_dogs': terrier_dogs,
        'i_users': i_users,
        'recent_bookings': recent_bookings,
        'middle_age_animals': middle_age_animals,
        'specific_sizes': specific_sizes,
        'not_cats': not_cats,
        'animals_with_breed': animals_with_breed,
        'user_animals': user_animals,
        'ivanov_animals': ivanov_animals,
    }
    
    return render(request, 'main/advanced_filters.html', context)


def time_based_filters(request):
    """
    Примеры использования двойного подчеркивания (__) для работы с датами и временем
    """
    today = timezone.now().date()
    
    # 1. Использование __ lookups для дат
    # Бронирования на следующую неделю
    next_week_start = today + timedelta(days=7)
    next_week_end = today + timedelta(days=14)
    next_week_bookings = Booking.objects.filter(
        start_date__gte=next_week_start,
        start_date__lt=next_week_end
    )
    
    # 2. Бронирования, созданные сегодня
    today_min = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    today_max = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))
    bookings_created_today = Booking.objects.filter(
        created_at__range=(today_min, today_max)
    )
    
    # 3. Отзывы за прошлый месяц
    last_month_start = today.replace(day=1) - timedelta(days=1)
    last_month_start = last_month_start.replace(day=1)
    last_month_end = today.replace(day=1) - timedelta(days=1)
    reviews_last_month = Review.objects.filter(
        date__gte=last_month_start,
        date__lte=last_month_end
    )
    
    # 4. Извлечение компонентов даты с помощью __year, __month, __day
    # Бронирования, начинающиеся в июне 2023 года
    june_bookings = Booking.objects.filter(
        start_date__year=2023,
        start_date__month=6
    )
    
    # 5. Использование __date для сравнения только даты в DateTimeField
    # Получить все бронирования, созданные сегодня
    today_bookings = Booking.objects.filter(created_at__date=today)
    
    # 6. Вычисление продолжительности бронирования с использованием ExpressionWrapper
    # Вычисляем продолжительность бронирования в днях
    bookings_with_duration = Booking.objects.annotate(
        duration=ExpressionWrapper(
            F('end_date') - F('start_date'),
            output_field=fields.IntegerField()
        )
    )
    
    # 7. Фильтрация по продолжительности
    # Долгосрочные бронирования (более 7 дней)
    long_bookings = bookings_with_duration.filter(duration__gt=7)
    
    context = {
        'next_week_bookings': next_week_bookings,
        'bookings_created_today': bookings_created_today,
        'reviews_last_month': reviews_last_month,
        'june_bookings': june_bookings,
        'today_bookings': today_bookings,
        'bookings_with_duration': bookings_with_duration,
        'long_bookings': long_bookings,
    }
    
    return render(request, 'main/time_filters.html', context)


# Представления для модели User

class UserListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка пользователей.
    Требует аутентификации пользователя.

    Attributes:
        model: Модель User для работы со списком пользователей
        template_name: Путь к шаблону для отображения списка
        context_object_name: Имя переменной контекста для списка пользователей
    """
    model = User
    template_name = 'main/user_list.html'
    context_object_name = 'users'


class UserDetailView(LoginRequiredMixin, DetailView):
    """
    Представление для отображения детальной информации о пользователе.
    Требует аутентификации пользователя.

    Attributes:
        model: Модель User для работы с данными пользователя
        template_name: Путь к шаблону для отображения информации
        context_object_name: Имя переменной контекста для объекта пользователя
    """
    model = User
    template_name = 'main/user_detail.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Добавление дополнительных данных в контекст шаблона.

        Returns:
            Dict[str, Any]: Расширенный контекст шаблона с дополнительными данными
        """
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['animals'] = user.animals.all()
        context['bookings'] = user.bookings.all()
        if hasattr(user, 'dogsitter'):
            context['is_dogsitter'] = True
            context['dogsitter_bookings'] = user.dogsitter.bookings.all()
        return context


class UserCreateView(CreateView):
    """
    Представление для создания нового пользователя.

    Attributes:
        model: Модель User для создания пользователя
        template_name: Путь к шаблону формы создания
        fields: Список полей формы для заполнения
    """
    model = User
    template_name = 'main/user_form.html'
    fields = ['email', 'first_name', 'last_name', 'password']


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для обновления данных пользователя.
    Требует аутентификации пользователя.

    Attributes:
        model: Модель User для обновления данных
        template_name: Путь к шаблону формы обновления
        fields: Список полей формы для редактирования
    """
    model = User
    template_name = 'main/user_form.html'
    fields = ['email', 'first_name', 'last_name']


class UserDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для удаления пользователя.
    Требует аутентификации пользователя.

    Attributes:
        model: Модель User для удаления пользователя
        template_name: Путь к шаблону подтверждения удаления
        success_url: URL для перенаправления после успешного удаления
    """
    model = User
    template_name = 'main/user_confirm_delete.html'
    success_url = '/users/'


# Представления для модели Booking

@login_required
def booking_cancel(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Отмена бронирования.
    Требует аутентификации пользователя.

    Args:
        request: Объект HTTP-запроса
        pk: Идентификатор бронирования

    Returns:
        HttpResponse: Перенаправление на страницу со списком бронирований

    Raises:
        Http404: Если бронирование не найдено
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.user != request.user and booking.dog_sitter.user != request.user:
        raise Http404("У вас нет прав для отмены этого бронирования")
    
    if booking.status not in [Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]:
        messages.error(request, "Невозможно отменить это бронирование")
        return redirect('booking_detail', pk=pk)
    
    booking.status = Booking.STATUS_CANCELLED
    booking.save()
    
    messages.success(request, "Бронирование успешно отменено")
    return redirect('booking_list')


@login_required
def booking_complete(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Завершение бронирования.
    Требует аутентификации пользователя.

    Args:
        request: Объект HTTP-запроса
        pk: Идентификатор бронирования

    Returns:
        HttpResponse: Перенаправление на страницу со списком бронирований

    Raises:
        Http404: Если бронирование не найдено
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.user != request.user and booking.dog_sitter.user != request.user:
        raise Http404("У вас нет прав для завершения этого бронирования")
    
    if booking.status != Booking.STATUS_CONFIRMED:
        messages.error(request, "Невозможно завершить это бронирование")
        return redirect('booking_detail', pk=pk)
    
    booking.status = Booking.STATUS_COMPLETED
    booking.save()
    
    messages.success(request, "Бронирование успешно завершено")
    return redirect('booking_list')


class BookingDetailView(LoginRequiredMixin, DetailView):
    """
    Представление для отображения детальной информации о бронировании.
    Требует аутентификации пользователя.

    Attributes:
        model: Модель Booking для работы с данными бронирования
        template_name: Путь к шаблону для отображения информации
        context_object_name: Имя переменной контекста для объекта бронирования
    """
    model = Booking
    template_name = 'main/booking_detail.html'
    context_object_name = 'booking'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Добавление дополнительных данных в контекст шаблона.

        Returns:
            Dict[str, Any]: Расширенный контекст шаблона с дополнительными данными
        """
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        
        context['can_cancel'] = (
            booking.status in [Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED] and
            (booking.user == self.request.user or booking.dog_sitter.user == self.request.user)
        )
        
        context['can_complete'] = (
            booking.status == Booking.STATUS_CONFIRMED and
            (booking.user == self.request.user or booking.dog_sitter.user == self.request.user)
        )
        
        context['can_review'] = (
            booking.status == Booking.STATUS_COMPLETED and
            booking.user == self.request.user and
            not hasattr(booking, 'review')
        )
        
        return context


# Представление для создания отзыва

class ReviewCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания отзыва о бронировании.
    Требует аутентификации пользователя.

    Attributes:
        template_name: Путь к шаблону формы создания отзыва
        fields: Список полей формы для заполнения
    """
    template_name = 'main/review_form.html'
    fields = ['rating', 'comment']

    def get_success_url(self) -> str:
        """
        Получение URL для перенаправления после успешного создания отзыва.

        Returns:
            str: URL страницы бронирования
        """
        return reverse('booking_detail', kwargs={'pk': self.object.booking.pk})

    def form_valid(self, form) -> HttpResponse:
        """
        Обработка валидной формы создания отзыва.

        Args:
            form: Объект формы с валидными данными

        Returns:
            HttpResponse: Перенаправление на страницу бронирования
        """
        form.instance.booking = get_object_or_404(Booking, pk=self.kwargs['booking_id'])
        form.instance.user = self.request.user
        return super().form_valid(form)


# Пример использования Booking Manager

def active_bookings(request: HttpRequest) -> HttpResponse:
    """
    Отображение списка активных бронирований.

    Args:
        request: Объект HTTP-запроса

    Returns:
        HttpResponse: Отрендеренная страница со списком активных бронирований
    """
    bookings: QuerySet[Booking] = Booking.objects.filter(
        status=Booking.STATUS_CONFIRMED,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).select_related('user', 'dog_sitter')

    context = {
        'bookings': bookings,
        'title': 'Активные бронирования'
    }
    return render(request, 'main/booking_list.html', context)


def current_bookings(request: HttpRequest) -> HttpResponse:
    """
    Отображение списка текущих бронирований пользователя.

    Args:
        request: Объект HTTP-запроса

    Returns:
        HttpResponse: Отрендеренная страница со списком текущих бронирований
    """
    bookings: QuerySet[Booking] = Booking.objects.filter(
        user=request.user,
        end_date__gte=timezone.now()
    ).select_related('dog_sitter')

    context = {
        'bookings': bookings,
        'title': 'Мои текущие бронирования'
    }
    return render(request, 'main/booking_list.html', context)


def future_bookings(request: HttpRequest) -> HttpResponse:
    """
    Отображение списка будущих бронирований.

    Args:
        request: Объект HTTP-запроса

    Returns:
        HttpResponse: Отрендеренная страница со списком будущих бронирований
    """
    bookings: QuerySet[Booking] = Booking.objects.filter(
        start_date__gt=timezone.now()
    ).select_related('user', 'dog_sitter')

    context = {
        'bookings': bookings,
        'title': 'Будущие бронирования'
    }
    return render(request, 'main/booking_list.html', context)


def long_term_bookings(request: HttpRequest) -> HttpResponse:
    """
    Отображение списка долгосрочных бронирований (более 7 дней).

    Args:
        request: Объект HTTP-запроса

    Returns:
        HttpResponse: Отрендеренная страница со списком долгосрочных бронирований
    """
    one_week = timezone.timedelta(days=7)
    bookings: QuerySet[Booking] = Booking.objects.annotate(
        duration=ExpressionWrapper(
            F('end_date') - F('start_date'),
            output_field=fields.DurationField()
        )
    ).filter(duration__gt=one_week)

    context = {
        'bookings': bookings,
        'title': 'Долгосрочные бронирования'
    }
    return render(request, 'main/booking_list.html', context)


def aggregation_annotation_examples(request):
    """
    Представление для демонстрации примеров использования агрегирования и аннотирования в Django ORM
    """
    context = {}
    
    # Пример 1: Базовое агрегирование - общая статистика системы
    system_stats = {
        'users_count': User.objects.count(),
        'animals_count': Animal.objects.count(),
        'dogsitters_count': DogSitter.objects.count(),
        'bookings_count': Booking.objects.count(),
        'reviews_count': Review.objects.count(),
        
        # Статистика по статусам бронирований
        'pending_bookings': Booking.objects.filter(status=Booking.STATUS_PENDING).count(),
        'confirmed_bookings': Booking.objects.filter(status=Booking.STATUS_CONFIRMED).count(),
        'completed_bookings': Booking.objects.filter(status=Booking.STATUS_COMPLETED).count(),
        'cancelled_bookings': Booking.objects.filter(status=Booking.STATUS_CANCELLED).count(),
        
        # Статистика по типам животных
        'dogs_count': Animal.objects.filter(type=Animal.DOG).count(),
        'cats_count': Animal.objects.filter(type=Animal.CAT).count(),
        'other_animals_count': Animal.objects.filter(type=Animal.OTHER).count(),
        
        # Агрегирование статистики бронирований
        'bookings_stats': Booking.objects.aggregate(
            total_price_sum=Sum('total_price'),
            avg_price=Avg('total_price'),
            max_price=Max('total_price'),
            min_price=Min('total_price'),
            avg_duration=Avg(F('end_date') - F('start_date'))
        ),
        
        # Агрегирование статистики отзывов
        'reviews_stats': Review.objects.aggregate(
            avg_rating=Avg('rating'),
            reviews_count=Count('id'),
            five_star_reviews=Count('id', filter=Q(rating=5)),
            four_star_reviews=Count('id', filter=Q(rating=4)),
            three_star_reviews=Count('id', filter=Q(rating=3)),
            two_star_reviews=Count('id', filter=Q(rating=2)),
            one_star_reviews=Count('id', filter=Q(rating=1))
        )
    }
    context['system_stats'] = system_stats
    
    # Пример 2: Аннотирование объектов - получение метрик для пользователей и догситтеров
    top_users = User.objects.annotate(
        bookings_count=Count('bookings'),
        animals_count=Count('animals'),
        total_spent=Sum('bookings__total_price', filter=Q(bookings__status=Booking.STATUS_COMPLETED)),
        completed_bookings=Count('bookings', filter=Q(bookings__status=Booking.STATUS_COMPLETED)),
        full_name=Concat('last_name', Value(' '), 'first_name', output_field=CharField()),
        last_booking_date=Max('bookings__start_date'),
        has_dogs=Case(
            When(animals__type=Animal.DOG, then=Value(True)),
            default=Value(False),
            output_field=IntegerField()
        ),
        has_cats=Case(
            When(animals__type=Animal.CAT, then=Value(True)),
            default=Value(False),
            output_field=IntegerField()
        )
    ).order_by('-bookings_count')[:10]
    
    top_dogsitters = DogSitter.objects.annotate(
        bookings_count=Count('bookings'),
        total_earnings=Sum('bookings__total_price', filter=Q(bookings__status=Booking.STATUS_COMPLETED)),
        clients_count=Count('bookings__user', distinct=True),
        animals_count=Count('bookings__animals', distinct=True),
        avg_client_rating=Avg('bookings__review__rating'),
        full_name=Concat('last_name', Value(' '), 'first_name', output_field=CharField()),
        last_booking_date=Max('bookings__start_date'),
        reviews_count=Count('bookings__review')
    ).order_by('-bookings_count')[:10]
    
    context['top_users'] = top_users
    context['top_dogsitters'] = top_dogsitters
    
    # Пример 3: Сложное аннотирование с группировкой - статистика по месяцам и размерам животных
    bookings_by_month = Booking.objects.annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        bookings_count=Count('id'),
        total_revenue=Sum('total_price'),
        avg_price=Avg('total_price'),
        completed_count=Count('id', filter=Q(status=Booking.STATUS_COMPLETED)),
        cancelled_count=Count('id', filter=Q(status=Booking.STATUS_CANCELLED)),
        animals_count=Count('animals', distinct=True),
        services_count=Count('services', distinct=True)
    ).order_by('-month')
    
    # Статистика по размерам животных
    animal_size_stats = Animal.objects.values('size').annotate(
        count=Count('id'),
        avg_bookings=Count('bookings') / Count('id', distinct=True),
        bookings_count=Count('bookings'),
        unique_owners=Count('user', distinct=True),
        with_special_needs=Count('id', filter=~Q(special_needs='') & ~Q(special_needs__isnull=True))
    ).order_by('size')
    
    # Используем методы моделей для получения комплексных статистик
    # Выберем пользователя и догситтера для демонстрации
    demo_user = User.objects.annotate(bookings_count=Count('bookings')).order_by('-bookings_count').first()
    demo_dogsitter = DogSitter.objects.annotate(bookings_count=Count('bookings')).order_by('-bookings_count').first()
    
    context['bookings_by_month'] = bookings_by_month
    context['animal_size_stats'] = animal_size_stats
    
    if demo_user:
        context['user_bookings_stats'] = demo_user.get_bookings_stats()
        context['user_bookings_by_month'] = demo_user.get_bookings_by_month_annotated()
        context['user_animals_stats'] = demo_user.get_animals_with_bookings_stats()
    
    if demo_dogsitter:
        context['dogsitter_statistics'] = demo_dogsitter.get_statistics()
        context['dogsitter_bookings_by_month'] = demo_dogsitter.get_bookings_by_month()
        context['dogsitter_clients_stats'] = demo_dogsitter.get_clients_with_stats()
    
    return render(request, 'main/aggregation_examples.html', context)

@login_required
def animal_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Удаление животного.
    Требует аутентификации пользователя.

    Args:
        request: Объект HTTP-запроса
        pk: Идентификатор животного

    Returns:
        HttpResponse: Перенаправление на страницу со списком животных

    Raises:
        Http404: Если животное не найдено или у пользователя нет прав на удаление
    """
    animal = get_object_or_404(Animal, pk=pk)
    
    if animal.user != request.user:
        raise Http404("У вас нет прав для удаления этого животного")
    
    if animal.bookings.filter(
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
        end_date__gte=timezone.now()
    ).exists():
        messages.error(request, "Невозможно удалить животное с активными бронированиями")
        return redirect('animal_detail', pk=pk)
    
    animal.delete()
    messages.success(request, "Животное успешно удалено")
    return redirect('animal_list')

@login_required
def add_animal_to_booking(request: HttpRequest, booking_id: int, animal_id: int) -> HttpResponse:
    """
    Добавление животного в бронирование.
    Требует аутентификации пользователя.

    Args:
        request: Объект HTTP-запроса
        booking_id: Идентификатор бронирования
        animal_id: Идентификатор животного

    Returns:
        HttpResponse: Перенаправление на страницу бронирования

    Raises:
        Http404: Если бронирование или животное не найдены
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    animal = get_object_or_404(Animal, pk=animal_id)
    
    if booking.user != request.user:
        raise Http404("У вас нет прав для изменения этого бронирования")
    
    if animal.user != request.user:
        raise Http404("Вы можете добавлять только своих животных")
    
    if booking.status != Booking.STATUS_PENDING:
        messages.error(request, "Можно добавлять животных только в неподтвержденные бронирования")
        return redirect('booking_detail', pk=booking_id)
    
    # Проверяем, не пересекается ли это бронирование с другими для этого животного
    conflicting_bookings = animal.bookings.filter(
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
        start_date__lt=booking.end_date,
        end_date__gt=booking.start_date
    ).exclude(pk=booking_id)
    
    if conflicting_bookings.exists():
        messages.error(request, "У животного есть пересекающиеся бронирования на эти даты")
        return redirect('booking_detail', pk=booking_id)
    
    booking.animals.add(animal)
    messages.success(request, f"Животное {animal.name} добавлено в бронирование")
    return redirect('booking_detail', pk=booking_id)

@login_required
def toggle_dogsitter_availability(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Переключение статуса доступности догситтера.
    Требует аутентификации пользователя.

    Args:
        request: Объект HTTP-запроса
        pk: Идентификатор догситтера

    Returns:
        HttpResponse: Перенаправление на страницу профиля догситтера

    Raises:
        Http404: Если догситтер не найден или у пользователя нет прав
    """
    dogsitter = get_object_or_404(DogSitter, pk=pk)
    
    if dogsitter.user != request.user:
        raise Http404("У вас нет прав для изменения статуса этого догситтера")
    
    dogsitter.is_available = not dogsitter.is_available
    dogsitter.save()
    
    status = "доступен" if dogsitter.is_available else "недоступен"
    messages.success(request, f"Ваш статус изменен на: {status}")
    return redirect('dogsitter_profile', pk=pk)

@login_required
def create_review(request: HttpRequest, booking_id: int) -> HttpResponse:
    """
    Создание отзыва о бронировании.
    Требует аутентификации пользователя.

    Args:
        request: Объект HTTP-запроса
        booking_id: Идентификатор бронирования

    Returns:
        HttpResponse: Перенаправление на страницу бронирования или форму создания отзыва

    Raises:
        Http404: Если бронирование не найдено или у пользователя нет прав
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    
    if booking.user != request.user:
        raise Http404("Вы можете оставлять отзывы только о своих бронированиях")
    
    if booking.status != Booking.STATUS_COMPLETED:
        messages.error(request, "Можно оставлять отзывы только о завершенных бронированиях")
        return redirect('booking_detail', pk=booking_id)
    
    if hasattr(booking, 'review'):
        messages.error(request, "Вы уже оставили отзыв об этом бронировании")
        return redirect('booking_detail', pk=booking_id)
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
        
        if not (1 <= rating <= 5):
            messages.error(request, "Оценка должна быть от 1 до 5")
            return redirect('create_review', booking_id=booking_id)
        
        review = Review.objects.create(
            booking=booking,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        # Обновляем рейтинг догситтера
        dogsitter = booking.dog_sitter
        avg_rating = Review.objects.filter(
            booking__dog_sitter=dogsitter,
            booking__status=Booking.STATUS_COMPLETED
        ).aggregate(Avg('rating'))['rating__avg']
        
        dogsitter.rating = round(avg_rating, 1) if avg_rating else 0.0
        dogsitter.save()
        
        messages.success(request, "Спасибо за ваш отзыв!")
        return redirect('booking_detail', pk=booking_id)
    
    return render(request, 'main/review_form.html', {'booking': booking})

@login_required
def cancel_booking_with_refund(request, booking_id):
    """Отмена бронирования с возвратом оплаты и условными редиректами"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Проверяем права и условия
    if booking.user != request.user:
        messages.error(request, "Вы не можете отменить чужое бронирование")
        return redirect('booking_list')
    
    if booking.status != Booking.STATUS_CONFIRMED:
        messages.error(request, "Можно отменить только подтверждённое бронирование")
        return redirect('booking_detail', pk=booking_id)
    
    # Проверяем срок до начала бронирования
    if (booking.start_date - timezone.now().date()).days < 2:
        messages.error(request, "Отмена возможна не менее чем за 48 часов до начала")
        return redirect('booking_detail', pk=booking_id)
    
    try:
        # Отменяем бронирование
        booking.status = Booking.STATUS_CANCELLED
        booking.save()
        
        # Возвращаем оплату (условно)
        messages.success(request, "Бронирование отменено. Средства будут возвращены в течение 3 рабочих дней")
        return redirect('booking_list')
        
    except Exception as e:
        messages.error(request, "Произошла ошибка при отмене бронирования")
        return redirect('booking_detail', pk=booking_id)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def booking_detail_api(request: HttpRequest, pk: int) -> Response:
    """
    API-представление для получения и обновления информации о бронировании.
    Требует аутентификации пользователя.

    Args:
        request: Объект HTTP-запроса
        pk: Идентификатор бронирования

    Returns:
        Response: JSON-ответ с данными бронирования или результатом обновления

    Raises:
        Http404: Если бронирование не найдено
    """
    booking = get_object_or_404(Booking, pk=pk)

    if request.method == 'GET':
        data = {
            'id': booking.id,
            'status': booking.get_status_display(),
            'start_date': booking.start_date,
            'end_date': booking.end_date,
            'total_price': str(booking.total_price),
            'user': {
                'id': booking.user.id,
                'name': f"{booking.user.first_name} {booking.user.last_name}"
            },
            'dog_sitter': {
                'id': booking.dog_sitter.id,
                'name': f"{booking.dog_sitter.user.first_name} {booking.dog_sitter.user.last_name}"
            } if booking.dog_sitter else None,
            'animals': [
                {
                    'id': animal.id,
                    'name': animal.name,
                    'type': animal.get_type_display()
                }
                for animal in booking.animals.all()
            ],
            'services': [
                {
                    'id': service.id,
                    'name': service.name,
                    'price': str(service.price)
                }
                for service in booking.services.all()
            ]
        }
        return Response(data)

    elif request.method == 'PATCH':
        if 'status' in request.data:
            booking.status = request.data['status']
            booking.save()
            return Response({'status': 'updated'})
        return Response({'error': 'No status provided'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_bookings_by_user(request: HttpRequest) -> Response:
    """
    API-представление для получения списка бронирований пользователя (для администраторов).
    Требует аутентификации пользователя и прав администратора.

    Args:
        request: Объект HTTP-запроса с параметрами фильтрации
            - user_id: ID пользователя
            - status: статус бронирования
            - start_date: начальная дата
            - end_date: конечная дата

    Returns:
        Response: JSON-ответ со списком бронирований пользователя

    Raises:
        PermissionDenied: Если у пользователя нет прав администратора
    """
    if not request.user.is_staff:
        return Response(
            {"error": "Требуются права администратора"},
            status=status.HTTP_403_FORBIDDEN
        )

    user_id = request.GET.get('user_id')
    if not user_id:
        return Response(
            {"error": "Не указан ID пользователя"},
            status=status.HTTP_400_BAD_REQUEST
        )

    bookings: QuerySet[Booking] = Booking.objects.filter(user_id=user_id)

    # Фильтрация по статусу
    booking_status = request.GET.get('status')
    if booking_status:
        bookings = bookings.filter(status=booking_status)

    # Фильтрация по датам
    start_date = request.GET.get('start_date')
    if start_date:
        bookings = bookings.filter(start_date__gte=start_date)

    end_date = request.GET.get('end_date')
    if end_date:
        bookings = bookings.filter(end_date__lte=end_date)

    data = [
        {
            'id': booking.id,
            'status': booking.get_status_display(),
            'start_date': booking.start_date,
            'end_date': booking.end_date,
            'total_price': str(booking.total_price),
            'dog_sitter': {
                'id': booking.dog_sitter.id,
                'name': f"{booking.dog_sitter.user.first_name} {booking.dog_sitter.user.last_name}"
            } if booking.dog_sitter else None,
            'animals': [
                {
                    'id': animal.id,
                    'name': animal.name,
                    'type': animal.get_type_display()
                }
                for animal in booking.animals.all()
            ],
            'services': [
                {
                    'id': service.id,
                    'name': service.name,
                    'price': str(service.price)
                }
                for service in booking.services.all()
            ]
        }
        for booking in bookings
    ]

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_animals_by_user(request: HttpRequest) -> Response:
    """
    API-представление для получения списка животных пользователя (для администраторов).
    Требует аутентификации пользователя и прав администратора.

    Args:
        request: Объект HTTP-запроса с параметрами фильтрации
            - user_id: ID пользователя
            - type: тип животного
            - size: размер животного

    Returns:
        Response: JSON-ответ со списком животных пользователя

    Raises:
        PermissionDenied: Если у пользователя нет прав администратора
    """
    if not request.user.is_staff:
        return Response(
            {"error": "Требуются права администратора"},
            status=status.HTTP_403_FORBIDDEN
        )

    user_id = request.GET.get('user_id')
    if not user_id:
        return Response(
            {"error": "Не указан ID пользователя"},
            status=status.HTTP_400_BAD_REQUEST
        )

    animals: QuerySet[Animal] = Animal.objects.filter(user_id=user_id)

    # Фильтрация по типу животного
    animal_type = request.GET.get('type')
    if animal_type:
        animals = animals.filter(type=animal_type)

    # Фильтрация по размеру
    size = request.GET.get('size')
    if size:
        animals = animals.filter(size=size)

    data = [
        {
            'id': animal.id,
            'name': animal.name,
            'type': animal.get_type_display(),
            'breed': animal.breed,
            'age': animal.age,
            'size': animal.get_size_display(),
            'bookings_count': animal.bookings.count(),
            'active_bookings': animal.bookings.filter(
                status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
                end_date__gte=timezone.now()
            ).count()
        }
        for animal in animals
    ]

    return Response(data)

@api_view(['GET'])
def animal_list_api(request: HttpRequest) -> Response:
    """
    API-представление для получения списка животных с возможностью фильтрации.

    Args:
        request: Объект HTTP-запроса с параметрами фильтрации
            - type: тип животного
            - size: размер животного
            - breed: порода животного
            - age_min: минимальный возраст
            - age_max: максимальный возраст

    Returns:
        Response: JSON-ответ со списком отфильтрованных животных
    """
    animals: QuerySet[Animal] = Animal.objects.all()

    # Фильтрация по типу животного
    animal_type = request.GET.get('type')
    if animal_type:
        animals = animals.filter(type=animal_type)

    # Фильтрация по размеру
    size = request.GET.get('size')
    if size:
        animals = animals.filter(size=size)

    # Фильтрация по породе
    breed = request.GET.get('breed')
    if breed:
        animals = animals.filter(breed__icontains=breed)

    # Фильтрация по возрасту
    age_min = request.GET.get('age_min')
    if age_min:
        animals = animals.filter(age__gte=int(age_min))

    age_max = request.GET.get('age_max')
    if age_max:
        animals = animals.filter(age__lte=int(age_max))

    data = [
        {
            'id': animal.id,
            'name': animal.name,
            'type': animal.get_type_display(),
            'breed': animal.breed,
            'age': animal.age,
            'size': animal.get_size_display(),
            'owner': {
                'id': animal.user.id,
                'name': f"{animal.user.first_name} {animal.user.last_name}"
            }
        }
        for animal in animals
    ]

    return Response(data)

@api_view(['GET', 'PUT', 'DELETE'])
def animal_detail_api(request, pk):
    """API endpoint для работы с конкретным животным"""
    try:
        animal = Animal.objects.get(pk=pk)
    except Animal.DoesNotExist:
        return Response({"error": "Животное не найдено"}, status=404)
    
    if animal.user != request.user and not request.user.is_superuser:
        return Response({"error": "У вас нет прав для этого действия"}, status=403)
    
    if request.method == 'GET':
        data = {
            'id': animal.id,
            'name': animal.name,
            'type': animal.type,
            'breed': animal.breed,
            'age': animal.age,
            'size': animal.size,
            'special_needs': animal.special_needs,
            'photo': animal.photo.url if animal.photo else None,
            'bookings_count': animal.bookings.count()
        }
        return Response(data)
    
    elif request.method == 'PUT':
        if 'name' in request.data:
            animal.name = request.data['name']
        if 'type' in request.data:
            animal.type = request.data['type']
        if 'breed' in request.data:
            animal.breed = request.data['breed']
        if 'age' in request.data:
            animal.age = request.data['age']
        if 'size' in request.data:
            animal.size = request.data['size']
        if 'special_needs' in request.data:
            animal.special_needs = request.data['special_needs']
        if 'photo' in request.FILES:
            animal.photo = request.FILES['photo']
        
        animal.save()
        return Response({"message": "Животное успешно обновлено"})
    
    elif request.method == 'DELETE':
        animal.delete()
        return Response({"message": "Животное успешно удалено"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_animals_by_user(request):
    """API endpoint для получения животных, сгруппированных по пользователям (только для администраторов)"""
    if not request.user.is_superuser:
        return Response({"error": "Доступ запрещен"}, status=403)
    
    users_with_animals = User.objects.filter(animals__isnull=False).distinct()
    result = []
    
    for user in users_with_animals:
        user_animals = Animal.objects.filter(user=user).order_by('name')
        animals_data = []
        
        for animal in user_animals:
            animal_data = {
                'id': animal.id,
                'name': animal.name,
                'type': animal.type,
                'breed': animal.breed,
                'age': animal.age,
                'size': animal.size,
                'special_needs': animal.special_needs,
                'photo': animal.photo.url if animal.photo else None,
                'bookings_count': animal.bookings.count()
            }
            animals_data.append(animal_data)
        
        user_data = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'animals': animals_data
        }
        result.append(user_data)
    
    return Response(result)

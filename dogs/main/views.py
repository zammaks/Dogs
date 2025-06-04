from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Count, Avg, Sum, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncMonth, Concat
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User, Animal, Booking, DogSitter, Service, Review


def index(request):
    """Главная страница"""
    # Получаем количество животных, бронирований и догситтеров для статистики
    animals_count = Animal.objects.count()
    bookings_count = Booking.objects.count()
    dogsitters_count = DogSitter.objects.count()
    
    # Получаем 5 догситтеров с самым высоким рейтингом
    top_dogsitters = DogSitter.objects.order_by('-rating')[:5]
    
    context = {
        'animals_count': animals_count,
        'bookings_count': bookings_count,
        'dogsitters_count': dogsitters_count,
        'top_dogsitters': top_dogsitters,
    }
    return render(request, 'main/index.html', context)


def search_dogsitters(request):
    min_rating = request.GET.get('min_rating', 0)
    
    dogsitters = DogSitter.objects.all()
    
    if min_rating:
        dogsitters = dogsitters.filter(rating__gte=float(min_rating))
    
    if 'has_reviews' in request.GET:
        dogsitters = dogsitters.annotate(review_count=Count('bookings__review')).filter(review_count__gt=0)
    
    # Показываем только активных догситтеров (заходивших на сайт за последние 30 дней)
    if 'active_only' in request.GET:
        active_date = timezone.now() - timezone.timedelta(days=30)
        dogsitters = dogsitters.filter(last_login__gte=active_date)
    
    # Сортировка результатов
    dogsitters = dogsitters.order_by('-rating')
    
    context = {
        'dogsitters': dogsitters,
        'min_rating': min_rating,
    }
    return render(request, 'main/dogsitters_list.html', context)


class AnimalListView(ListView):
    """Представление списка животных с использованием filter() в ListView"""
    model = Animal
    template_name = 'main/animal_list.html'
    context_object_name = 'animals'
    paginate_by = 10
    
    def get_queryset(self):
        """Переопределяем метод для фильтрации результатов"""
        # Получаем базовый QuerySet
        queryset = super().get_queryset()
        
        # Получаем параметры фильтрации из GET-запроса
        animal_type = self.request.GET.get('type')
        animal_size = self.request.GET.get('size')
        
        # Применяем фильтры, если они указаны
        if animal_type:
            queryset = queryset.filter(type=animal_type)
        
        if animal_size:
            queryset = queryset.filter(size=animal_size)
            
        # Фильтрация по владельцу, если указан ID владельца
        user_id = self.request.GET.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Сложная фильтрация с использованием Q-объектов (для поиска)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(breed__icontains=search_query)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        # Добавляем списки возможных значений для фильтров
        context['animal_types'] = Animal.ANIMAL_TYPE_CHOICES
        context['animal_sizes'] = Animal.ANIMAL_SIZE_CHOICES
        
        # Добавляем текущие значения фильтров
        context['current_type'] = self.request.GET.get('type', '')
        context['current_size'] = self.request.GET.get('size', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


def booking_list(request):
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


def api_animal_search(request):
    """API-представление для поиска животных с использованием filter()"""
    # Получаем параметры поиска
    query = request.GET.get('query', '')
    animal_type = request.GET.get('type', '')
    
    # Базовый QuerySet
    animals = Animal.objects.all()
    
    # Применяем фильтрацию
    if query:
        animals = animals.filter(
            Q(name__icontains=query) | 
            Q(breed__icontains=query)
        )
    
    if animal_type:
        animals = animals.filter(type=animal_type)
    
    # Преобразуем результаты в список словарей для JSON-ответа
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


def advanced_filter_examples(request):

    expensive_bookings = Booking.objects.filter(total_price__gt=5000)
    

    terrier_dogs = Animal.objects.filter(breed__contains="терьер")
    
 
    i_users = User.objects.filter(last_name__startswith="И")
    
 
    week_ago = timezone.now().date() - timedelta(days=7)
    recent_bookings = Booking.objects.filter(start_date__gte=week_ago)
    
    # 1.5 - Поиск по диапазону значений
    # Животные среднего возраста (от 3 до 8 лет)
    middle_age_animals = Animal.objects.filter(age__range=(3, 8))
    
    # 1.6 - Поиск по списку значений
    # Поиск животных определенных размеров
    specific_sizes = Animal.objects.filter(
        size__in=[Animal.SIZE_SMALL, Animal.SIZE_LARGE]
    )
    

    not_cats = Animal.objects.exclude(type=Animal.CAT)
    
    # 1.8 - Проверка на NULL / NOT NULL
    # Животные с указанной породой
    animals_with_breed = Animal.objects.filter(breed__isnull=False)
    
    # ПРИМЕР 2: Использование __ для доступа к связанным моделям
    
    # 2.1 - Простая связь ForeignKey
    # Все животные пользователя с ID=1
    user_animals = Animal.objects.filter(user__id=1)
    
    # 2.2 - Фильтрация по полям связанной модели
    # Все животные, чьи владельцы имеют фамилию "Иванов"
    ivanov_animals = Animal.objects.filter(user__last_name="Иванов")
    
    # 2.3 - Цепочка связей через несколько моделей
    # Все отзывы для бронирований с крупными собаками
    large_dog_reviews = Review.objects.filter(
        booking__animals__size=Animal.SIZE_LARGE,
        booking__animals__type=Animal.DOG
    ).distinct()
    
    # 2.4 - Сложная фильтрация с использованием Q-объектов и связанных моделей
    # Догситтеры, которые работали с крупными собаками или с кошками
    sitters_with_experience = DogSitter.objects.filter(
        Q(bookings__animals__type=Animal.DOG, bookings__animals__size=Animal.SIZE_LARGE) |
        Q(bookings__animals__type=Animal.CAT)
    ).distinct()
    
    # 2.5 - Работа с обратными связями
    # Пользователи, у которых есть активные бронирования
    active_users = User.objects.filter(
        bookings__status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
    ).distinct()
    
    # 2.6 - Аннотации со связанными моделями
    # Подсчет количества животных у каждого пользователя
    users_with_animal_count = User.objects.annotate(
        animal_count=Count('animals')
    )
    
    # 2.7 - Агрегация по связанным моделям
    # Общая стоимость всех бронирований для каждого догситтера
    sitters_earnings = DogSitter.objects.annotate(
        total_earnings=Sum('bookings__total_price')
    )
    
    # 2.8 - Сложная аннотация с условиями на связанных моделях
    # Количество крупных собак у каждого пользователя
    users_with_large_dogs = User.objects.annotate(
        large_dog_count=Count('animals', filter=Q(animals__type=Animal.DOG, animals__size=Animal.SIZE_LARGE))
    )
    
    # Формируем контекст с результатами
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
        'large_dog_reviews': large_dog_reviews,
        'sitters_with_experience': sitters_with_experience,
        'active_users': active_users,
        'users_with_animal_count': users_with_animal_count,
        'sitters_earnings': sitters_earnings,
        'users_with_large_dogs': users_with_large_dogs,
    }
    
    return render(request, 'main/advanced_queries.html', context)


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
    model = User
    template_name = 'main/user_list.html'
    context_object_name = 'users'
    

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'main/user_detail.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['dogs'] = user.get_all_dogs()
        context['cats'] = user.get_all_cats()
        context['upcoming_bookings'] = user.get_upcoming_bookings()
        context['active_bookings_count'] = user.get_active_bookings_count()
        return context


class UserCreateView(CreateView):
    model = User
    template_name = 'main/user_form.html'
    fields = ['email', 'first_name', 'last_name', 'password']


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'main/user_form.html'
    fields = ['email', 'first_name', 'last_name']


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'main/user_confirm_delete.html'
    success_url = '/users/'


# Представления для модели Booking

@login_required
def booking_cancel(request, pk):
    """
    Отмена бронирования
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    if not booking.can_be_cancelled():
        messages.error(request, "Это бронирование нельзя отменить")
        # Использование get_absolute_url вместо хардкода URL
        return HttpResponseRedirect(booking.get_absolute_url())
    
    booking.status = Booking.STATUS_CANCELLED
    booking.save()
    messages.success(request, "Бронирование успешно отменено")
    
    # Использование get_absolute_url для перенаправления
    return HttpResponseRedirect(booking.get_absolute_url())


@login_required
def booking_complete(request, pk):
    """
    Завершение бронирования
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.status != Booking.STATUS_CONFIRMED:
        messages.error(request, "Завершить можно только подтвержденное бронирование")
        # Использование get_absolute_url
        return HttpResponseRedirect(booking.get_absolute_url())
    
    booking.status = Booking.STATUS_COMPLETED
    booking.save()
    messages.success(request, "Бронирование успешно завершено")
    
    # Перенаправление на страницу создания отзыва с использованием reverse
    return HttpResponseRedirect(reverse('review_create', kwargs={'booking_id': booking.id}))


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'main/booking_detail.html'
    context_object_name = 'booking'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        
        # Получаем ссылки на связанные объекты с использованием get_absolute_url
        context['user_url'] = booking.get_user_url()
        
        if booking.dog_sitter:
            context['dogsitter_url'] = booking.get_dogsitter_url()
            
            
        animals = booking.animals.all()
        for animal in animals:
            animal.url = animal.get_absolute_url()
            
        context['animals'] = animals
        
        # Формируем ссылки действий с использованием get_absolute_url
        context['edit_url'] = booking.get_edit_url()
        context['cancel_url'] = booking.get_cancel_url()
        context['complete_url'] = booking.get_complete_url()
        
        return context


# Представление для создания отзыва

class ReviewCreateView(LoginRequiredMixin, CreateView):
    template_name = 'main/review_form.html'
    fields = ['rating', 'comment']

    def get_success_url(self):
        # Использование reverse для получения URL
        return f'/bookings/{self.kwargs["booking_id"]}/'
    
    def form_valid(self, form):
        # Привязка к бронированию
        booking_id = self.kwargs.get('booking_id')
        booking = get_object_or_404(Booking, pk=booking_id)
        form.instance.booking = booking
        form.instance.date = timezone.now()
        
        return super().form_valid(form)


# Пример использования Booking Manager

def active_bookings(request):
    """
    Страница с активными бронированиями
    """
    # Используем метод active() из модельного менеджера
    bookings = Booking.objects.active()
    
    return render(request, 'main/active_bookings.html', {
        'bookings': bookings,
        'title': 'Активные бронирования'
    })


def current_bookings(request):
    """
    Страница с текущими бронированиями
    """
    # Используем метод current() из модельного менеджера
    bookings = Booking.objects.current()
    
    return render(request, 'main/current_bookings.html', {
        'bookings': bookings,
        'title': 'Текущие бронирования'
    })


def future_bookings(request):
    """
    Страница с предстоящими бронированиями
    """
    # Используем метод future() из модельного менеджера
    bookings = Booking.objects.future()
    
    return render(request, 'main/future_bookings.html', {
        'bookings': bookings,
        'title': 'Предстоящие бронирования'
    })


def long_term_bookings(request):
    """
    Страница с долгосрочными бронированиями
    """
    # Используем метод long_term() из модельного менеджера
    bookings = Booking.objects.long_term()
    
    return render(request, 'main/long_term_bookings.html', {
        'bookings': bookings,
        'title': 'Долгосрочные бронирования'
    })


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
def animal_delete(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    
    if animal.user != request.user:
        messages.error(request, "У вас нет прав для удаления этого животного")
        return redirect('animal_list')
    
    animal.delete()
    messages.success(request, f"Животное {animal.name} было успешно удалено")
    return redirect('animal_list')

@login_required
def add_animal_to_booking(request, booking_id, animal_id):
    """Добавление животного в бронирование с обработкой ошибок"""
    try:
        booking = Booking.objects.get(pk=booking_id)
        animal = Animal.objects.get(pk=animal_id)
        
        # Проверки
        if booking.user != request.user:
            messages.error(request, "Это не ваше бронирование")
            return redirect('booking_list')
            
        if animal.user != request.user:
            messages.error(request, "Это не ваше животное")
            return redirect('booking_detail', pk=booking_id)
            
        if booking.status != Booking.STATUS_PENDING:
            messages.error(request, "Можно добавлять животных только в ожидающие бронирования")
            return redirect('booking_detail', pk=booking_id)
        
        # Добавляем животное
        booking.animals.add(animal)
        messages.success(request, f"{animal.name} добавлен(а) в бронирование")
        
        return redirect('booking_detail', pk=booking_id)
        
    except Booking.DoesNotExist:
        raise Http404("Бронирование не найдено")
    except Animal.DoesNotExist:
        raise Http404("Животное не найдено")

@login_required
def toggle_dogsitter_availability(request, pk):
    """Переключение доступности догситтера с редиректом на реферер"""
    dogsitter = get_object_or_404(DogSitter, user=request.user)
    
    # Переключаем статус
    dogsitter.is_available = not dogsitter.is_available
    dogsitter.save()
    
    # Сообщение о результате
    status = "доступен" if dogsitter.is_available else "недоступен"
    messages.info(request, f"Ваш статус изменен на: {status}")
    
    # Редирект на предыдущую страницу или профиль
    next_page = request.META.get('HTTP_REFERER')
    if next_page:
        return redirect(next_page)
    return redirect('dogsitter_profile')

@login_required
def create_review(request, booking_id):
    """Создание отзыва с проверками и редиректами"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Проверяем, можно ли оставить отзыв
    if booking.user != request.user:
        messages.error(request, "Вы не можете оставить отзыв на чужое бронирование")
        return redirect('booking_list')
        
    if booking.status != Booking.STATUS_COMPLETED:
        messages.error(request, "Отзыв можно оставить только на завершённое бронирование")
        return redirect('booking_detail', pk=booking_id)
        
    if hasattr(booking, 'review'):
        messages.error(request, "Вы уже оставили отзыв на это бронирование")
        return redirect('booking_detail', pk=booking_id)
    
    if request.method == 'POST':
        # Создаем отзыв
        review = Review.objects.create(
            booking=booking,
            rating=request.POST.get('rating'),
            comment=request.POST.get('comment')
        )
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
def booking_detail_api(request, pk):
    """
    API endpoint для получения и обновления информации о бронировании
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    # Проверяем, что пользователь имеет доступ к этому бронированию
    if booking.user != request.user and booking.dog_sitter.user != request.user:
        return Response({"error": "У вас нет доступа к этому бронированию"}, status=403)
    
    if request.method == 'GET':
        # Получаем связанные данные
        booking_data = {
            'id': booking.id,
            'start_date': booking.start_date,
            'end_date': booking.end_date,
            'status': booking.status,
            'total_price': str(booking.total_price),
            'dog_sitter': {
                'id': booking.dog_sitter.id,
                'user': {
                    'first_name': booking.dog_sitter.user.first_name,
                    'last_name': booking.dog_sitter.user.last_name
                }
            },
            'animals': [{
                'id': animal.id,
                'name': animal.name,
                'type': animal.type,
                'size': animal.size
            } for animal in booking.animals.all()],
            'services': [{
                'id': service.id,
                'name': service.name,
                'price': str(service.price)
            } for service in booking.services.all()]
        }
        return Response(booking_data)
    
    elif request.method == 'PATCH':
        # Проверяем, можно ли редактировать бронирование
        if booking.status not in ['pending', 'confirmed']:
            return Response({"error": "Нельзя редактировать завершенное или отмененное бронирование"}, status=400)
        
        # Обновляем данные
        if 'start_date' in request.data:
            booking.start_date = request.data['start_date']
        if 'end_date' in request.data:
            booking.end_date = request.data['end_date']
        if 'services' in request.data:
            booking.services.set(request.data['services'])
        
        try:
            booking.save()
            
            # Возвращаем обновленные данные
            return Response({
                'id': booking.id,
                'start_date': booking.start_date,
                'end_date': booking.end_date,
                'status': booking.status,
                'total_price': str(booking.total_price),
                'services': [{
                    'id': service.id,
                    'name': service.name,
                    'price': str(service.price)
                } for service in booking.services.all()]
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

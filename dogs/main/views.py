from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Avg, Sum, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta

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
        for animal in animals[:20]  # Ограничиваем до 20 результатов
    ]
    
    return JsonResponse({'results': animals_data})


def advanced_filter_examples(request):

    expensive_bookings = Booking.objects.filter(total_price__gt=5000)
    
    # 1.2 - Поиск по подстроке (contains)
    # Поиск животных с породой, содержащей "терьер" (без учёта регистра)
    terrier_dogs = Animal.objects.filter(breed__icontains="терьер")
    
    # 1.3 - Поиск по началу или концу строки
    # Пользователи, чья фамилия начинается на "И"
    i_users = User.objects.filter(last_name__startswith="И")
    
    # 1.4 - Работа с датами
    # Бронирования за последние 7 дней
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

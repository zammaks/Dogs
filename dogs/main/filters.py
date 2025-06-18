from django_filters import rest_framework as filters
from .models import DogSitter
from django.db.models import Q
from django.utils import timezone

class DogSitterFilter(filters.FilterSet):
    min_rating = filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='average_rating', lookup_expr='lte')
    min_experience = filters.NumberFilter(field_name='experience_years', lookup_expr='gte')
    max_experience = filters.NumberFilter(field_name='experience_years', lookup_expr='lte')
    min_reviews = filters.NumberFilter(field_name='total_reviews', lookup_expr='gte')
    name = filters.CharFilter(method='filter_by_name')
    has_reviews = filters.BooleanFilter(field_name='total_reviews', method='filter_has_reviews')
    is_available = filters.BooleanFilter(method='filter_is_available')
    sort_by = filters.CharFilter(method='apply_sorting')

    def filter_by_name(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(user__first_name__icontains=value) |
                Q(user__last_name__icontains=value)
            )
        return queryset

    def filter_has_reviews(self, queryset, name, value):
        if value is True:
            return queryset.filter(total_reviews__gt=0)
        elif value is False:
            return queryset.filter(total_reviews=0)
        return queryset

    def filter_is_available(self, queryset, name, value):
        if value is True:
            return queryset.filter(is_blocked=False).exclude(
                bookings__status='confirmed',
                bookings__start_date__lte=timezone.now().date(),
                bookings__end_date__gte=timezone.now().date()
            )
        elif value is False:
            return queryset.filter(
                Q(is_blocked=True) |
                Q(bookings__status='confirmed',
                  bookings__start_date__lte=timezone.now().date(),
                  bookings__end_date__gte=timezone.now().date())
            ).distinct()
        return queryset

    def apply_sorting(self, queryset, name, value):
        valid_fields = {
            'rating': '-average_rating',
            'rating_asc': 'average_rating',
            'experience': '-experience_years',
            'experience_asc': 'experience_years',
            'reviews': '-total_reviews',
            'reviews_asc': 'total_reviews',
            'name': 'user__last_name',
            'name_desc': '-user__last_name'
        }
        
        if value in valid_fields:
            return queryset.order_by(valid_fields[value])
        return queryset

    class Meta:
        model = DogSitter
        fields = [
            'min_rating', 'max_rating',
            'min_experience', 'max_experience',
            'min_reviews', 'name',
            'has_reviews', 'is_available',
            'sort_by'
        ] 
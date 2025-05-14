from django.contrib import admin
from .models import User, Animal, Service, DogSitter, Booking, Review

class AnimalInline(admin.TabularInline):
    model = Animal
    extra = 1

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'email', 'phone', 'address')
    list_filter = ('last_name', 'first_name')
    inlines = [AnimalInline]
    search_fields = ('last_name', 'first_name', 'email', 'phone')

    def get_animal_count(self, obj):
        return obj.animals.count()

    get_animal_count.short_description = "Количество животных"

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'custom_type', 'breed', 'age', 'size', 'special_needs')
    list_filter = ('type', 'size')
    list_display_links = ('name', 'type')
    search_fields = ('name', 'breed', 'custom_type')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    list_filter = ('price',)
    search_fields = ('name',)

@admin.register(DogSitter)
class DogSitterAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'email', 'phone', 'rating')
    list_filter = ('last_name', 'first_name', 'rating')
    search_fields = ('last_name', 'first_name', 'email', 'phone')
    filter_horizontal = ('accepted_bookings',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'dog_sitter', 'total_price')
    list_filter = ('start_date', 'end_date', 'dog_sitter')
    date_hierarchy = 'start_date'
    raw_id_fields = ('user', 'dog_sitter')
    filter_horizontal = ('animals', 'services')
    search_fields = ('user__last_name', 'user__first_name', 'dog_sitter__last_name', 'dog_sitter__first_name')

    @admin.display(description="Длительность (дни)")
    def get_duration(self, obj):
        return (obj.end_date - obj.start_date).days



@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'date')
    list_filter = ('rating', 'date')
    readonly_fields = ('date',)
    search_fields = ('booking__user__last_name', 'booking__user__first_name', 'comment')
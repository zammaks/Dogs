from django.contrib import admin
from .models import User, DogSitter, Animal, Booking, Service, Review

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name']
    search_fields = ['email', 'first_name', 'last_name']

@admin.register(DogSitter)
class DogSitterAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'rating', 'experience_years']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = "Полное имя"

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'breed', 'age', 'size']
    list_filter = ['type', 'size']
    search_fields = ['name', 'breed']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'dog_sitter', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['user__email', 'dog_sitter__user__email']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rating', 'date']
    list_filter = ['rating', 'date']
    search_fields = ['comment']
from django.contrib import admin
from .models import User, Animal, Boarding, Order, Review, Service

class AnimalInline(admin.TabularInline):
    model = Animal
    extra = 1

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'get_animal_count')
    list_filter = ('role',)
    inlines = [AnimalInline]
    search_fields = ('name', 'email')

    def get_animal_count(self, obj):
        return obj.animals.count()

    get_animal_count.short_description = "Количество животных"

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'breed', 'age')
    list_filter = ('type', 'breed', 'age')
    list_display_links = ('name', 'type')
    search_fields = ('name', 'breed')

@admin.register(Boarding)
class BoardingAdmin(admin.ModelAdmin):
    list_display = ('user', 'price_per_day', 'capacity')
    list_filter = ('price_per_day', 'capacity')
    raw_id_fields = ('user',)
    filter_horizontal = ('services',)  # Если бы у Boarding было поле ManyToMany

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('animal', 'boarding', 'start_date', 'end_date', 'get_duration')
    list_filter = ('start_date', 'end_date')
    date_hierarchy = 'start_date'
    raw_id_fields = ('animal', 'boarding')
    search_fields = ('animal__name', 'boarding__user__name')

    @admin.display(description="Длительность (дни)")
    def get_duration(self, obj):
        return (obj.end_date - obj.start_date).days

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'rating', 'date')
    list_filter = ('rating', 'date')
    readonly_fields = ('date',)
    search_fields = ('order__animal__name', 'comment')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('boarding', 'name', 'price')
    list_filter = ('price',)
    search_fields = ('name',)
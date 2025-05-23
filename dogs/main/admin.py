from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.utils.html import format_html
from .models import User, DogSitter, Animal, Booking, Service, Review, BookingAnimal
from .utils import generate_booking_pdf, generate_dogsitter_report_pdf

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'phone', 'is_active']
    list_filter = ['is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    readonly_fields = ['date_joined', 'last_login']
    actions = ['deactivate_users', 'activate_users']

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        messages.success(request, f'Деактивировано пользователей: {queryset.count()}')
    deactivate_users.short_description = "Деактивировать выбранных пользователей"

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        messages.success(request, f'Активировано пользователей: {queryset.count()}')
    activate_users.short_description = "Активировать выбранных пользователей"

@admin.register(DogSitter)
class DogSitterAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 'rating', 'experience_years', 'is_active', 
        'total_bookings', 'total_earnings', 'show_documents'
    ]
    list_filter = ['rating', 'experience_years']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    actions = ['generate_pdf_reports', 'mark_as_inactive', 'mark_as_active']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = "Полное имя"

    def total_bookings(self, obj):
        return obj.bookings.count()
    total_bookings.short_description = "Всего бронирований"

    def total_earnings(self, obj):
        return obj.calculate_total_earnings()
    total_earnings.short_description = "Общий заработок"

    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    is_active.short_description = "Активен"

    def show_documents(self, obj):
        documents = []
        if obj.passport_scan:
            documents.append(format_html('<a href="{}" target="_blank">Паспорт</a>', obj.passport_scan.url))
        if obj.medical_certificate:
            documents.append(format_html('<a href="{}" target="_blank">Мед. справка</a>', obj.medical_certificate.url))
        if obj.experience_certificate:
            documents.append(format_html('<a href="{}" target="_blank">Сертификат</a>', obj.experience_certificate.url))
        return format_html(' | '.join(documents)) if documents else "Нет документов"
    show_documents.short_description = "Документы"

    def generate_pdf_reports(self, request, queryset):
        if len(queryset) == 1:
            dogsitter = queryset[0]
            return generate_dogsitter_report_pdf(dogsitter)
        else:
            import zipfile
            import io
            
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                for dogsitter in queryset:
                    pdf_buffer = io.BytesIO()
                    p = generate_dogsitter_report_pdf(dogsitter)
                    pdf_buffer.write(p.content)
                    zip_file.writestr(f'dogsitter_report_{dogsitter.id}.pdf', pdf_buffer.getvalue())
            
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="dogsitter_reports.zip"'
            return response
    generate_pdf_reports.short_description = "Сгенерировать PDF отчеты"

    def mark_as_inactive(self, request, queryset):
        for dogsitter in queryset:
            dogsitter.user.is_active = False
            dogsitter.user.save()
        messages.success(request, f'Деактивировано догситтеров: {queryset.count()}')
    mark_as_inactive.short_description = "Отметить как неактивных"

    def mark_as_active(self, request, queryset):
        for dogsitter in queryset:
            dogsitter.user.is_active = True
            dogsitter.user.save()
        messages.success(request, f'Активировано догситтеров: {queryset.count()}')
    mark_as_active.short_description = "Отметить как активных"

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'breed', 'age', 'size', 'get_owner', 'total_bookings', 'show_photo']
    list_filter = ['type', 'size', 'age']
    search_fields = ['name', 'breed', 'user__email', 'user__first_name', 'user__last_name']
    actions = ['mark_as_available', 'mark_as_unavailable']

    def get_owner(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_owner.short_description = "Владелец"

    def total_bookings(self, obj):
        return obj.bookings.count()
    total_bookings.short_description = "Всего бронирований"

    def show_photo(self, obj):
        if obj.photo:
            return format_html('<a href="{}" target="_blank">Просмотреть фото</a>', obj.photo.url)
        return "Нет фото"
    show_photo.short_description = "Фотография"

    def mark_as_available(self, request, queryset):
        queryset.update(is_available=True)
        messages.success(request, f'Отмечено как доступные: {queryset.count()} животных')
    mark_as_available.short_description = "Отметить как доступные"

    def mark_as_unavailable(self, request, queryset):
        queryset.update(is_available=False)
        messages.success(request, f'Отмечено как недоступные: {queryset.count()} животных')
    mark_as_unavailable.short_description = "Отметить как недоступные"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'dog_sitter', 'start_date', 'end_date', 
        'status', 'total_price', 'created_at', 'show_documents'
    ]
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['user__email', 'dog_sitter__user__email']
    actions = ['generate_pdf_documents', 'mark_as_completed', 'mark_as_cancelled']

    def show_documents(self, obj):
        documents = []
        if obj.contract_file:
            documents.append(format_html('<a href="{}" target="_blank">Договор</a>', obj.contract_file.url))
        if obj.payment_receipt:
            documents.append(format_html('<a href="{}" target="_blank">Чек</a>', obj.payment_receipt.url))
        if obj.additional_documents:
            documents.append(format_html('<a href="{}" target="_blank">Доп. документы</a>', obj.additional_documents.url))
        return format_html(' | '.join(documents)) if documents else "Нет документов"
    show_documents.short_description = "Документы"

    def generate_pdf_documents(self, request, queryset):
        if len(queryset) == 1:
            booking = queryset[0]
            return generate_booking_pdf(booking)
        else:
            import zipfile
            import io
            
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                for booking in queryset:
                    pdf_buffer = io.BytesIO()
                    p = generate_booking_pdf(booking)
                    pdf_buffer.write(p.content)
                    zip_file.writestr(f'booking_{booking.id}.pdf', pdf_buffer.getvalue())
            
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="bookings.zip"'
            return response
    generate_pdf_documents.short_description = "Сгенерировать PDF документы"

    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='confirmed').update(
            status='completed',
            updated_at=timezone.now()
        )
        messages.success(request, f'Отмечено как завершенные: {updated} бронирований')
    mark_as_completed.short_description = "Отметить как завершенные"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.exclude(status__in=['completed', 'cancelled']).update(
            status='cancelled',
            updated_at=timezone.now()
        )
        messages.success(request, f'Отмечено как отмененные: {updated} бронирований')
    mark_as_cancelled.short_description = "Отметить как отмененные"

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active', 'total_bookings']
    list_filter = ['price']
    search_fields = ['name', 'description']
    actions = ['mark_as_active', 'mark_as_inactive']

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = "Активна"

    def total_bookings(self, obj):
        return obj.bookings.count()
    total_bookings.short_description = "Всего бронирований"

    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)
        messages.success(request, f'Активировано услуг: {queryset.count()}')
    mark_as_active.short_description = "Отметить как активные"

    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
        messages.success(request, f'Деактивировано услуг: {queryset.count()}')
    mark_as_inactive.short_description = "Отметить как неактивные"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rating', 'date', 'get_dogsitter', 'get_client']
    list_filter = ['rating', 'date']
    search_fields = ['comment', 'booking__user__email', 'booking__dog_sitter__user__email']
    actions = ['mark_as_verified', 'mark_as_unverified']

    def get_dogsitter(self, obj):
        return f"{obj.booking.dog_sitter.user.first_name} {obj.booking.dog_sitter.user.last_name}"
    get_dogsitter.short_description = "Догситтер"

    def get_client(self, obj):
        return f"{obj.booking.user.first_name} {obj.booking.user.last_name}"
    get_client.short_description = "Клиент"

    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True)
        messages.success(request, f'Верифицировано отзывов: {queryset.count()}')
    mark_as_verified.short_description = "Отметить как проверенные"

    def mark_as_unverified(self, request, queryset):
        queryset.update(is_verified=False)
        messages.success(request, f'Отмечено как непроверенные: {queryset.count()}')
    mark_as_unverified.short_description = "Отметить как непроверенные"

@admin.register(BookingAnimal)
class BookingAnimalAdmin(admin.ModelAdmin):
    list_display = ['booking', 'animal', 'added_at']
    list_filter = ['added_at']
    search_fields = ['booking__id', 'animal__name', 'special_notes']
    readonly_fields = ['added_at']
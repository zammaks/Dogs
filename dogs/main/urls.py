from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api
from users.views import UserProfileView, UserPhotoListCreateView, UserPhotoDetailView, DeleteAccountView
from . import views

router = DefaultRouter()
router.register(r'dogsitters', views_api.DogSitterViewSet, basename='dogsitter')
router.register(r'bookings', views_api.BookingViewSet, basename='booking')
router.register(r'animals', views_api.AnimalViewSet, basename='animal')
router.register(r'services', views_api.ServiceViewSet, basename='service')

urlpatterns = [
    path('', views_api.index, name='index'),
    path('', include(router.urls)),
    path('auth/register/', views_api.register_view, name='api_register'),
    path('auth/login/', views_api.login_view, name='api_login'),
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/me/photos/', UserPhotoListCreateView.as_view(), name='user-photos'),
    path('users/me/photos/<int:pk>/', UserPhotoDetailView.as_view(), name='user-photo-detail'),
    path('bookings/<int:pk>/cancel/', views_api.cancel_booking, name='booking-cancel'),
    path('users/me/delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('statistics/', views_api.get_statistics, name='api-statistics'),
    path('sentry-debug/', views_api.sentry_debug, name='sentry-debug'),
    
    # Маршруты для животных
    path('animals/<int:pk>/delete/', views.animal_delete, name='animal_delete'),
    
    # Маршруты для бронирований
    path('bookings/<int:booking_id>/add-animal/<int:animal_id>/', 
         views.add_animal_to_booking, name='add_animal_to_booking'),
    path('bookings/<int:booking_id>/cancel-refund/', 
         views.cancel_booking_with_refund, name='cancel_booking_with_refund'),
    
    # Маршруты для догситтеров
    path('dogsitters/<int:pk>/toggle-availability/', 
         views.toggle_dogsitter_availability, name='toggle_dogsitter_availability'),
    
    # Маршруты для отзывов
    path('bookings/<int:booking_id>/review/create/', 
         views.create_review, name='create_review'),
    path('bookings/<int:pk>/', views.booking_detail_api, name='booking_detail_api'),
    path('dogsitters/<int:pk>/block/', views_api.block_dogsitter, name='block_dogsitter'),
    path('dogsitters/<int:pk>/unblock/', views_api.block_dogsitter, name='unblock_dogsitter'),
    path('api/bookings-by-user/', views.admin_bookings_by_user, name='admin_bookings_by_user'),
    path('api/animals-by-user/', views.admin_animals_by_user, name='admin_animals_by_user'),
] 
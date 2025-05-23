from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api
from users.views import UserProfileView, UserPhotoListCreateView, UserPhotoDetailView, DeleteAccountView
from . import views

router = DefaultRouter()
router.register(r'dogsitters', views_api.DogSitterViewSet)
router.register(r'bookings', views_api.BookingViewSet, basename='booking')

urlpatterns = [
    path('', views_api.index, name='index'),
    path('api/', include(router.urls)),
    path('api/auth/register/', views_api.register_view, name='api_register'),
    path('api/auth/login/', views_api.login_view, name='api_login'),
    path('api/users/me/', UserProfileView.as_view(), name='user-profile'),
    path('api/users/me/photos/', UserPhotoListCreateView.as_view(), name='user-photos'),
    path('api/users/me/photos/<int:pk>/', UserPhotoDetailView.as_view(), name='user-photo-detail'),
    path('api/bookings/<int:pk>/cancel/', views_api.cancel_booking, name='booking-cancel'),
    path('api/users/me/delete/', DeleteAccountView.as_view(), name='delete-account'),
    
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
] 
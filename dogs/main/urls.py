from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api
from users.views import UserProfileView, UserPhotoListCreateView, UserPhotoDetailView, DeleteAccountView

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
] 
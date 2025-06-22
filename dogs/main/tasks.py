from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.conf import settings
from users.models import User
from main.models import Booking
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from dogs.celery import app

@shared_task
def check_inactive_users():
    """
    Проверяет неактивных пользователей и отправляет им уведомления
    """
    threshold = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(last_login__lt=threshold, is_active=True)
    
    for user in inactive_users:
        send_mail(
            'Мы скучаем по вам!',
            'Вы давно не заходили на наш сайт. Возвращайтесь, у нас много интересного!',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    
    return f"Отправлено {inactive_users.count()} уведомлений"

@shared_task
def send_daily_statistics():
    """
    Отправляет ежедневную статистику администраторам
    """
    today = timezone.now().date()
    new_users = User.objects.filter(date_joined__date=today).count()
    new_bookings = Booking.objects.filter(created_at__date=today).count()
    
    admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
    
    message = f"""
    Статистика за {today}:
    - Новых пользователей: {new_users}
    - Новых бронирований: {new_bookings}
    """
    
    send_mail(
        'Ежедневная статистика',
        message,
        settings.DEFAULT_FROM_EMAIL,
        admin_emails,
        fail_silently=True,
    )
    
    return "Статистика отправлена"

@shared_task
def cleanup_old_sessions():
    """
    Очищает старые сессии из базы данных
    """
    threshold = timezone.now() - timedelta(days=7)
    old_sessions = Session.objects.filter(expire_date__lt=threshold)
    count = old_sessions.count()
    old_sessions.delete()
    
    return f"Удалено {count} старых сессий"

@shared_task(name='main.tasks.send_profile_update_notification')
def send_profile_update_notification(user_id):
    """
    Отправляет уведомление о успешном обновлении профиля
    """
    print(f"Starting send_profile_update_notification for user_id: {user_id}")
    try:
        channel_layer = get_channel_layer()
        print(f"Got channel layer: {channel_layer}")
        
        group_name = f"user_{user_id}"
        message = {
            "type": "notification_message",
            "message": "Ваш профиль успешно обновлен"
        }
        print(f"Sending to group {group_name}: {message}")
        
        # Отправляем уведомление в WebSocket
        async_to_sync(channel_layer.group_send)(group_name, message)
        print("Message sent successfully")
        
        return "Уведомление отправлено"
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Ошибка отправки уведомления: {str(e)}" 
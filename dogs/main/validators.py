from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


def validate_dogsitter_client_compatibility(dogsitter, client):
    """
    Валидатор для проверки совместимости догситтера и клиента
    
    Args:
        dogsitter: объект DogSitter
        client: объект User (клиент)
        
    Raises:
        ValidationError: если догситтер и клиент несовместимы
    """
    compatibility = dogsitter.get_compatibility_with_client(client)
    
    if not compatibility['compatible']:
        raise ValidationError(
            _('%(reason)s'),
            params={'reason': compatibility['reason']},
            code='incompatible_dogsitter_client'
        )


def validate_new_dogsitter_experience_restriction(dogsitter, client):
    """
    Специализированный валидатор для ограничения новых догситтеров
    
    Args:
        dogsitter: объект DogSitter
        client: объект User (клиент)
        
    Raises:
        ValidationError: если новый догситтер пытается обслужить опытного клиента
    """
    if dogsitter.is_new_dogsitter() and client.is_experienced_client():
        raise ValidationError(
            _('Новые догситтеры (с опытом менее 3 месяцев и менее 3 завершенных бронирований) '
              'не могут обслуживать опытных клиентов. Опытным считается клиент с 5+ завершенными '
              'бронированиями и стажем использования сервиса от 6 месяцев.'),
            code='new_dogsitter_experienced_client'
        )


def validate_booking_compatibility(booking_data):
    """
    Валидатор для проверки совместимости при создании бронирования
    
    Args:
        booking_data: словарь с данными бронирования
        
    Raises:
        ValidationError: если бронирование не может быть создано
    """
    from .models import DogSitter, User
    
    try:
        dogsitter = DogSitter.objects.get(id=booking_data.get('dog_sitter'))
        client = User.objects.get(id=booking_data.get('user'))
        
        validate_new_dogsitter_experience_restriction(dogsitter, client)
        
    except (DogSitter.DoesNotExist, User.DoesNotExist):
        raise ValidationError(
            _('Догситтер или клиент не найден'),
            code='invalid_dogsitter_or_client'
        )


class DogsitterClientCompatibilityValidator:
    """
    Класс-валидатор для проверки совместимости догситтера и клиента
    """
    
    def __init__(self, min_client_experience_months=6, min_client_bookings=5, 
                 max_dogsitter_bookings=3, max_dogsitter_months=3):
        self.min_client_experience_months = min_client_experience_months
        self.min_client_bookings = min_client_bookings
        self.max_dogsitter_bookings = max_dogsitter_bookings
        self.max_dogsitter_months = max_dogsitter_months
    
    def __call__(self, dogsitter, client):
        """
        Проверяет совместимость с настраиваемыми параметрами
        
        Args:
            dogsitter: объект DogSitter
            client: объект User (клиент)
            
        Raises:
            ValidationError: если несовместимы
        """
        # Проверяем, является ли клиент опытным
        client_completed_bookings = client.bookings.filter(status='completed').count()
        client_months = (timezone.now() - client.registration_date).days / 30
        
        is_experienced_client = (
            client_completed_bookings >= self.min_client_bookings and 
            client_months >= self.min_client_experience_months
        )
        
        # Проверяем, является ли догситтер новым
        dogsitter_completed_bookings = dogsitter.bookings.filter(status='completed').count()
        dogsitter_months = (timezone.now() - dogsitter.user.registration_date).days / 30
        
        is_new_dogsitter = (
            dogsitter_completed_bookings <= self.max_dogsitter_bookings and 
            dogsitter_months <= self.max_dogsitter_months
        )
        
        # Если догситтер новый, а клиент опытный - несовместимы
        if is_new_dogsitter and is_experienced_client:
            raise ValidationError(
                _('Новые догситтеры не могут обслуживать опытных клиентов. '
                  'Догситтер: %(dogsitter_info)s, Клиент: %(client_info)s'),
                params={
                    'dogsitter_info': f'{dogsitter_completed_bookings} бронирований, {dogsitter_months:.1f} месяцев',
                    'client_info': f'{client_completed_bookings} бронирований, {client_months:.1f} месяцев'
                },
                code='incompatible_experience_levels'
            ) 
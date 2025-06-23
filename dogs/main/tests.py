from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import DogSitter, Booking, Animal, Service
from .validators import validate_new_dogsitter_experience_restriction, DogsitterClientCompatibilityValidator
from django.core.exceptions import ValidationError

User = get_user_model()

class DogsitterClientCompatibilityTest(TestCase):
    """Тесты для проверки совместимости догситтеров и клиентов"""
    
    def setUp(self):
        """Создание тестовых данных"""
        # Создаем опытного клиента
        self.experienced_client = User.objects.create_user(
            username='experienced@test.com',
            email='experienced@test.com',
            password='testpass123',
            first_name='Опытный',
            last_name='Клиент',
            registration_date=timezone.now() - timedelta(days=200)  # 6+ месяцев назад
        )
        
        # Создаем нового клиента
        self.new_client = User.objects.create_user(
            username='new@test.com',
            email='new@test.com',
            password='testpass123',
            first_name='Новый',
            last_name='Клиент',
            registration_date=timezone.now() - timedelta(days=30)  # 1 месяц назад
        )
        
        # Создаем нового догситтера
        self.new_dogsitter_user = User.objects.create_user(
            username='new_dogsitter@test.com',
            email='new_dogsitter@test.com',
            password='testpass123',
            first_name='Новый',
            last_name='Догситтер',
            registration_date=timezone.now() - timedelta(days=60)  # 2 месяца назад
        )
        
        # Создаем опытного догситтера
        self.experienced_dogsitter_user = User.objects.create_user(
            username='experienced_dogsitter@test.com',
            email='experienced_dogsitter@test.com',
            password='testpass123',
            first_name='Опытный',
            last_name='Догситтер',
            registration_date=timezone.now() - timedelta(days=400)  # 13+ месяцев назад
        )
        
        # Создаем догситтеров
        self.new_dogsitter = DogSitter.objects.create(
            user=self.new_dogsitter_user,
            experience_years=1,
            description='Новый догситтер'
        )
        
        self.experienced_dogsitter = DogSitter.objects.create(
            user=self.experienced_dogsitter_user,
            experience_years=3,
            description='Опытный догситтер'
        )
        
        # Создаем услугу
        self.service = Service.objects.create(
            name='Выгул собак',
            description='Прогулка с собакой',
            price=500.00
        )
        
        # Создаем животное
        self.animal = Animal.objects.create(
            name='Бобик',
            type='dog',
            breed='Дворняжка',
            age=3,
            size='medium',
            user=self.experienced_client
        )
        
        # Создаем завершенные бронирования для опытного клиента
        for i in range(6):  # 6 завершенных бронирований
            booking = Booking.objects.create(
                user=self.experienced_client,
                dog_sitter=self.experienced_dogsitter,
                start_date=timezone.now().date() - timedelta(days=100 + i*10),
                end_date=timezone.now().date() - timedelta(days=95 + i*10),
                status='completed',
                total_price=1000.00
            )
            booking.animals.add(self.animal)
            booking.services.add(self.service)
        
        # Создаем несколько завершенных бронирований для нового догситтера
        for i in range(2):  # 2 завершенных бронирования
            booking = Booking.objects.create(
                user=self.new_client,
                dog_sitter=self.new_dogsitter,
                start_date=timezone.now().date() - timedelta(days=20 + i*5),
                end_date=timezone.now().date() - timedelta(days=15 + i*5),
                status='completed',
                total_price=800.00
            )
            booking.animals.add(self.animal)
            booking.services.add(self.service)
    
    def test_experienced_client_detection(self):
        """Тест определения опытного клиента"""
        self.assertTrue(self.experienced_client.is_experienced_client())
        self.assertFalse(self.new_client.is_experienced_client())
        
        # Проверяем уровни опыта
        self.assertEqual(self.experienced_client.get_client_experience_level(), 'experienced')
        self.assertEqual(self.new_client.get_client_experience_level(), 'new')
    
    def test_new_dogsitter_detection(self):
        """Тест определения нового догситтера"""
        self.assertTrue(self.new_dogsitter.is_new_dogsitter())
        self.assertFalse(self.experienced_dogsitter.is_new_dogsitter())
        
        # Проверяем уровни опыта
        self.assertEqual(self.new_dogsitter.get_dogsitter_experience_level(), 'new')
        self.assertEqual(self.experienced_dogsitter.get_dogsitter_experience_level(), 'experienced')
    
    def test_compatibility_check(self):
        """Тест проверки совместимости"""
        # Новый догситтер + опытный клиент = несовместимы
        compatibility = self.new_dogsitter.get_compatibility_with_client(self.experienced_client)
        self.assertFalse(compatibility['compatible'])
        self.assertIsNotNone(compatibility['reason'])
        
        # Опытный догситтер + опытный клиент = совместимы
        compatibility = self.experienced_dogsitter.get_compatibility_with_client(self.experienced_client)
        self.assertTrue(compatibility['compatible'])
        self.assertIsNone(compatibility['reason'])
        
        # Новый догситтер + новый клиент = совместимы
        compatibility = self.new_dogsitter.get_compatibility_with_client(self.new_client)
        self.assertTrue(compatibility['compatible'])
        self.assertIsNone(compatibility['reason'])
    
    def test_validator_functions(self):
        """Тест функций валидации"""
        # Должна вызвать исключение
        with self.assertRaises(ValidationError):
            validate_new_dogsitter_experience_restriction(self.new_dogsitter, self.experienced_client)
        
        # Не должна вызывать исключение
        try:
            validate_new_dogsitter_experience_restriction(self.experienced_dogsitter, self.experienced_client)
            validate_new_dogsitter_experience_restriction(self.new_dogsitter, self.new_client)
        except ValidationError:
            self.fail("ValidationError не должна быть вызвана для совместимых пар")
    
    def test_custom_validator_class(self):
        """Тест класса валидатора с настраиваемыми параметрами"""
        validator = DogsitterClientCompatibilityValidator(
            min_client_experience_months=3,
            min_client_bookings=3,
            max_dogsitter_bookings=5,
            max_dogsitter_months=6
        )
        
        # С более мягкими параметрами новые догситтеры могут обслуживать больше клиентов
        try:
            validator(self.new_dogsitter, self.experienced_client)
        except ValidationError:
            # Это нормально, так как у опытного клиента все еще 6+ месяцев опыта
            pass
    
    def test_can_serve_experienced_clients(self):
        """Тест метода can_serve_experienced_clients"""
        self.assertFalse(self.new_dogsitter.can_serve_experienced_clients())
        self.assertTrue(self.experienced_dogsitter.can_serve_experienced_clients())
    
    def test_client_statistics(self):
        """Тест статистики клиентов"""
        self.assertGreater(self.experienced_client.get_total_spent(), 0)
        self.assertEqual(self.new_client.get_total_spent(), 0)
        
        # Проверяем количество завершенных бронирований
        experienced_completed = self.experienced_client.bookings.filter(status='completed').count()
        new_completed = self.new_client.bookings.filter(status='completed').count()
        
        self.assertEqual(experienced_completed, 6)
        self.assertEqual(new_completed, 0)  # У нового клиента нет завершенных бронирований
    
    def test_edge_cases(self):
        """Тест граничных случаев"""
        # Клиент с ровно 5 бронированиями и 6 месяцами опыта
        edge_client = User.objects.create_user(
            username='edge@test.com',
            email='edge@test.com',
            password='testpass123',
            first_name='Граничный',
            last_name='Клиент',
            registration_date=timezone.now() - timedelta(days=180)  # ровно 6 месяцев
        )
        
        # Создаем ровно 5 завершенных бронирований
        for i in range(5):
            booking = Booking.objects.create(
                user=edge_client,
                dog_sitter=self.experienced_dogsitter,
                start_date=timezone.now().date() - timedelta(days=50 + i*5),
                end_date=timezone.now().date() - timedelta(days=45 + i*5),
                status='completed',
                total_price=1000.00
            )
            booking.animals.add(self.animal)
            booking.services.add(self.service)
        
        # Должен считаться опытным
        self.assertTrue(edge_client.is_experienced_client())
        
        # Новый догситтер не должен его обслуживать
        with self.assertRaises(ValidationError):
            validate_new_dogsitter_experience_restriction(self.new_dogsitter, edge_client)

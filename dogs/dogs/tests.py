from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
from main.models import Animal, Service, DogSitter
from django.utils import timezone
from datetime import datetime, timedelta

class AnimalTests(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        
        self.user = get_user_model().objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='ownerpass123'
        )

        self.dogsitter_user = get_user_model().objects.create_user(
            username='dogsitter',
            email='sitter@example.com',
            password='sitterpass123'
        )
        self.dogsitter = DogSitter.objects.create(
            user=self.dogsitter_user,
            experience_years=2,
            rating=4.5,
            description='Опытный догситтер'
        )

        self.animal = Animal.objects.create(
            name='Рекс',
            type='dog',
            breed='Лабрадор',
            age=3,
            size='large',
            user=self.user,
            special_needs='Нет особых потребностей'
        )
        # Создаем услугу
        self.service = Service.objects.create(
            name='Выгул собаки',
            description='Часовая прогулка с собакой',
            price=500.00
        )

    def test_animal_creation(self):
        self.assertEqual(self.animal.name, 'Рекс')
        self.assertEqual(self.animal.breed, 'Лабрадор')
        self.assertEqual(self.animal.user, self.user)

    def test_animal_type_choices(self):
        self.assertEqual(self.animal.type, 'dog')
        self.assertIn(self.animal.type, dict(Animal.ANIMAL_TYPE_CHOICES))

    def test_animal_size_choices(self):
        self.assertEqual(self.animal.size, 'large')
        self.assertIn(self.animal.size, dict(Animal.ANIMAL_SIZE_CHOICES))

    def test_animal_str_representation(self):
        self.assertEqual(str(self.animal), 'Рекс')

    def test_animal_get_size_display(self):
        self.assertEqual(self.animal.get_size_display_verbose(), "Крупный (более 25 кг)")

    def test_animal_is_available(self):
        self.assertTrue(self.animal.is_available)

    def test_service_creation(self):
        self.assertEqual(self.service.name, 'Выгул собаки')
        self.assertEqual(float(self.service.price), 500.00)

    def test_dogsitter_creation(self):
        """Тест создания профиля догситтера"""
        self.assertEqual(self.dogsitter.user, self.dogsitter_user)
        self.assertEqual(self.dogsitter.experience_years, 2)
        self.assertEqual(float(self.dogsitter.rating), 4.5)

    def test_dogsitter_rating_range(self):
        """Тест диапазона рейтинга догситтера"""
        self.assertTrue(0 <= self.dogsitter.rating <= 5)

    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.username, 'petowner')
        self.assertEqual(self.user.email, 'owner@example.com')
        self.assertTrue(self.user.check_password('ownerpass123')) 
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import UserProfile, DogSitter
from dogs.models import Dog

class UserTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone_number='+79991234567',
            city='Москва'
        )
        self.dogsitter = DogSitter.objects.create(
            user=self.user,
            experience=2,
            price_per_hour=500,
            description='Опытный выгульщик собак'
        )

    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_profile_creation(self):
        """Тест создания профиля пользователя"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.phone_number, '+79991234567')
        self.assertEqual(self.profile.city, 'Москва')

    def test_dogsitter_creation(self):
        """Тест создания профиля выгульщика"""
        self.assertEqual(self.dogsitter.user, self.user)
        self.assertEqual(self.dogsitter.experience, 2)
        self.assertEqual(self.dogsitter.price_per_hour, 500)

    def test_user_login(self):
        """Тест входа пользователя"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_user_logout(self):
        """Тест выхода пользователя"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_user_profile_update(self):
        """Тест обновления профиля пользователя"""
        self.client.login(username='testuser', password='testpass123')
        new_data = {
            'phone_number': '+79999999999',
            'city': 'Санкт-Петербург'
        }
        response = self.client.post(reverse('profile_update'), new_data)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.city, 'Санкт-Петербург') 
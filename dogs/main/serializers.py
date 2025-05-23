from rest_framework import serializers
from .models import User, DogSitter, Booking, Animal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = ['id', 'name', 'type', 'breed', 'size']

class DogSitterSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DogSitter
        fields = ['id', 'user', 'rating', 'description', 'experience_years']

class BookingSerializer(serializers.ModelSerializer):
    animals = AnimalSerializer(many=True, read_only=True)
    dog_sitter = DogSitterSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'start_date', 'end_date', 'status',
            'total_price', 'animals', 'dog_sitter'
        ]
        read_only_fields = ['total_price', 'status'] 
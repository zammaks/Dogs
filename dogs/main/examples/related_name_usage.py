"""
Примеры использования related_name в Django проекте.

Этот файл содержит демонстрационный код, показывающий практические 
примеры использования related_name из моделей проекта.
"""

from django.db import models
from main.models import User, Animal, DogSitter, Booking, Review, Service


# Пример 1: Получение животных пользователя
def example_user_animals():
    """
    Демонстрация доступа к животным пользователя через related_name="animals"
    """
    # Получаем пользователя по ID
    user = User.objects.get(id=1)
    
    # Получаем всех животных пользователя (related_name="animals")
    all_pets = user.animals.all()
    print(f"У пользователя {user} {all_pets.count()} животных")
    
    # Получаем только собак пользователя
    dogs = user.get_all_dogs()
    print(f"У пользователя {user} {dogs.count()} собак")
    
    # Фильтрация животных по дополнительным критериям
    large_animals = user.animals.filter(size=Animal.SIZE_LARGE)
    print(f"У пользователя {user} {large_animals.count()} крупных животных")
    
    # Создание нового животного для пользователя
    new_pet = user.animals.create(
        name="Барсик",
        type=Animal.CAT,
        size=Animal.SIZE_SMALL
    )
    print(f"Добавлено новое животное: {new_pet}")


# Пример 2: Бронирования и их связи
def example_bookings_related():
    """
    Демонстрация работы с бронированиями через related_name
    """
    # Получаем догситтера
    sitter = DogSitter.objects.get(id=1)
    
    # Получаем все бронирования догситтера (related_name="bookings")
    sitter_bookings = sitter.bookings.all()
    print(f"У догситтера {sitter} {sitter_bookings.count()} бронирований")
    
    # Получаем только активные бронирования
    active_bookings = sitter.bookings.filter(
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
    )
    print(f"Активных бронирований: {active_bookings.count()}")
    
    # Получаем отзывы по бронированиям догситтера
    # Обратите внимание на связь через двойное подчеркивание:
    # booking__dog_sitter связывает Review с DogSitter через Booking
    reviews = Review.objects.filter(booking__dog_sitter=sitter)
    print(f"У догситтера {sitter} {reviews.count()} отзывов")
    
    # Получение отзывов со средним рейтингом - альтернативный способ
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    print(f"Средний рейтинг догситтера: {avg_rating:.1f}")


# Пример 3: Работа с животными в бронировании
def example_booking_animals():
    """
    Демонстрация работы с животными в бронировании (ManyToMany relation)
    """
    # Получаем бронирование
    booking = Booking.objects.get(id=1)
    
    # Получаем всех животных в бронировании (related_name в ManyToManyField)
    animals_in_booking = booking.animals.all()
    print(f"В бронировании {booking.id} {animals_in_booking.count()} животных")
    
    # Фильтрация животных в бронировании
    dogs_in_booking = booking.animals.filter(type=Animal.DOG)
    print(f"В бронировании {booking.id} {dogs_in_booking.count()} собак")
    
    # Добавление нового животного в бронирование
    new_animal = Animal.objects.get(id=5)  # Получаем животное по ID
    booking.animals.add(new_animal)
    print(f"Животное {new_animal} добавлено в бронирование {booking.id}")
    
    # Удаление животного из бронирования
    booking.animals.remove(new_animal)
    print(f"Животное {new_animal} удалено из бронирования {booking.id}")
    
    # Получение списка бронирований для конкретного животного (обратная связь)
    animal = Animal.objects.get(id=3)
    animal_bookings = animal.bookings.all()
    print(f"У животного {animal} {animal_bookings.count()} бронирований")


# Пример 4: Работа с услугами в бронировании
def example_services_in_booking():
    """
    Демонстрация работы с услугами в бронировании (другой пример ManyToMany)
    """
    # Получаем бронирование
    booking = Booking.objects.get(id=1)
    
    # Получаем все услуги бронирования (related_name="bookings" в модели Service)
    services = booking.services.all()
    print(f"В бронировании {booking.id} {services.count()} услуг")
    
    # Получение стоимости услуг
    services_cost = sum(service.price for service in services)
    print(f"Общая стоимость услуг: {services_cost} руб.")
    
    # Получаем все бронирования, где заказана конкретная услуга
    service = Service.objects.get(id=2)
    bookings_with_service = service.bookings.all()
    print(f"Услуга '{service}' заказана в {bookings_with_service.count()} бронированиях")


# Пример 5: Получение списка владельцев животных с указанной породой
def example_complex_relations():
    """
    Демонстрация сложных связей через related_name
    """
    # Получаем список владельцев, у которых есть собаки породы 'Лабрадор'
    labrador_owners = User.objects.filter(animals__type=Animal.DOG, animals__breed='Лабрадор').distinct()
    print(f"Количество владельцев лабрадоров: {labrador_owners.count()}")
    
    # Получаем список всех бронирований, включающих крупных собак
    large_dog_bookings = Booking.objects.filter(
        animals__type=Animal.DOG,
        animals__size=Animal.SIZE_LARGE
    ).distinct()
    print(f"Бронирований с крупными собаками: {large_dog_bookings.count()}")
    
    # Получаем список догситтеров, которые обслуживали бронирования с крупными животными
    sitters_with_large_animals = DogSitter.objects.filter(
        bookings__animals__size=Animal.SIZE_LARGE
    ).distinct()
    print(f"Догситтеров с опытом работы с крупными животными: {sitters_with_large_animals.count()}")


# Функция для запуска всех примеров
def run_all_examples():
    """Запуск всех примеров использования related_name"""
    print("\n=== Пример 1: Животные пользователя ===")
    example_user_animals()
    
    print("\n=== Пример 2: Бронирования и догситтеры ===")
    example_bookings_related()
    
    print("\n=== Пример 3: Животные в бронировании ===")
    example_booking_animals()
    
    print("\n=== Пример 4: Услуги в бронировании ===")
    example_services_in_booking()
    
    print("\n=== Пример 5: Сложные связи ===")
    example_complex_relations()


if __name__ == "__main__":
    # Этот код выполнится только при непосредственном запуске файла
    print("Запуск примеров использования related_name в Django...")
    run_all_examples() 
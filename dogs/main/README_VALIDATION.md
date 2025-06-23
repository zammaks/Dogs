# Валидация совместимости догситтеров и клиентов

## Описание

Данный функционал реализует валидацию, которая ограничивает доступность новых догситтеров для опытных клиентов. Это помогает новым догситтерам набраться опыта с менее требовательными клиентами, прежде чем обслуживать опытных пользователей сервиса.

## Логика работы

### Определение опытного клиента

Клиент считается опытным, если выполняются **оба** условия:
- Имеет **5 или более** завершенных бронирований
- Использует сервис **6 или более месяцев** с момента регистрации

### Определение нового догситтера

Догситтер считается новым, если выполняются **оба** условия:
- Имеет **3 или менее** завершенных бронирований
- Зарегистрирован в сервисе **3 или менее месяца**

### Правила совместимости

- ✅ **Новый догситтер + Новый клиент** = Совместимы
- ✅ **Новый догситтер + Обычный клиент** = Совместимы  
- ❌ **Новый догситтер + Опытный клиент** = НЕ совместимы
- ✅ **Опытный догситтер + Любой клиент** = Совместимы

## Реализация

### Модели

#### User (users/models.py)

Добавлены методы:
- `is_experienced_client(min_bookings=5, min_months=6)` - проверяет, является ли клиент опытным
- `get_client_experience_level()` - возвращает уровень опыта ('new', 'regular', 'experienced')
- `get_total_spent()` - возвращает общую сумму потраченную на услуги

#### DogSitter (main/models.py)

Добавлены методы:
- `is_new_dogsitter(max_bookings=3, max_months=3)` - проверяет, является ли догситтер новым
- `get_dogsitter_experience_level()` - возвращает уровень опыта догситтера
- `can_serve_experienced_clients()` - проверяет, может ли обслуживать опытных клиентов
- `get_compatibility_with_client(client)` - проверяет совместимость с клиентом

### Валидаторы (main/validators.py)

#### Функции валидации:
- `validate_dogsitter_client_compatibility(dogsitter, client)` - основная функция валидации
- `validate_new_dogsitter_experience_restriction(dogsitter, client)` - специализированная валидация
- `validate_booking_compatibility(booking_data)` - валидация при создании бронирования

#### Класс валидатора:
- `DogsitterClientCompatibilityValidator` - настраиваемый валидатор с параметрами

### API

#### BookingViewSet (main/views_api.py)

Добавлены:
- Валидация в `perform_create()` и `create()`
- Новый endpoint `check_compatibility/` для проверки совместимости

#### Сериализатор (main/serializers.py)

BookingSerializer дополнен:
- `compatibility_info` - информация о совместимости
- `can_book` - можно ли создать бронирование
- Валидация в методах `validate()` и `create()`

## Использование

### Проверка совместимости через API

```bash
POST /api/bookings/check_compatibility/
{
    "dogsitter_id": 1
}
```

Ответ:
```json
{
    "compatible": false,
    "reason": "Новые догситтеры не могут обслуживать опытных клиентов",
    "dogsitter_level": "new",
    "client_level": "experienced",
    "dogsitter_info": {
        "completed_bookings": 2,
        "months_since_registration": 2.0,
        "is_new": true
    },
    "client_info": {
        "completed_bookings": 6,
        "months_since_registration": 6.7,
        "is_experienced": true
    }
}
```

### Программная проверка

```python
from main.models import DogSitter, User
from main.validators import validate_new_dogsitter_experience_restriction

# Получаем объекты
dogsitter = DogSitter.objects.get(id=1)
client = User.objects.get(id=1)

# Проверяем совместимость
try:
    validate_new_dogsitter_experience_restriction(dogsitter, client)
    print("Совместимы!")
except ValidationError as e:
    print(f"Несовместимы: {e}")
```

### Настройка параметров

```python
from main.validators import DogsitterClientCompatibilityValidator

# Создаем валидатор с кастомными параметрами
validator = DogsitterClientCompatibilityValidator(
    min_client_experience_months=3,  # Минимум 3 месяца опыта клиента
    min_client_bookings=3,           # Минимум 3 бронирования клиента
    max_dogsitter_bookings=5,        # Максимум 5 бронирований догситтера
    max_dogsitter_months=6           # Максимум 6 месяцев догситтера
)

# Используем валидатор
validator(dogsitter, client)
```

## Тестирование

Запуск тестов:
```bash
python manage.py test main.tests.DogsitterClientCompatibilityTest
```

Тесты покрывают:
- Определение опытных клиентов
- Определение новых догситтеров
- Проверку совместимости
- Валидаторы
- Граничные случаи

## Настройка

Параметры можно изменить в следующих местах:

1. **Модели** - изменить значения по умолчанию в методах
2. **Валидаторы** - настроить параметры в `DogsitterClientCompatibilityValidator`
3. **Админка** - добавить настройки в Django settings

## Мониторинг

Для отслеживания работы валидации можно:

1. Логировать попытки создания несовместимых бронирований
2. Отслеживать статистику по уровням опыта пользователей
3. Анализировать переходы догситтеров между уровнями опыта

## Будущие улучшения

1. **Динамические параметры** - настройка через админку
2. **Исключения** - возможность администратора разрешить несовместимые пары
3. **Уведомления** - информирование пользователей о причинах ограничений
4. **Аналитика** - статистика по совместимости и эффективности системы 
# Proxy Gateway
Веб-сервис для управления прокси-доступом с регистрацией пользователей, активационными ключами и десктопным клиентом.

---
## Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git

### Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/bemz2/proxy-gateway
cd proxy-gateway

# 2. Скопировать переменные окружения
cp .env.example .env

# 3. Запустить все сервисы
docker-compose up -d --build

# 4. Дождаться запуска (проверить health checks)
docker-compose ps

# 5. Открыть в браузере
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
```

### Проверка работы сервисов

```bash
# Проверить логи backend
docker-compose logs -f backend

# Проверить логи celery worker (здесь будут email с ключами)
docker-compose logs -f celery-worker

# Проверить логи celery beat (планировщик задач)
docker-compose logs -f celery-beat

# Проверить статус всех контейнеров
docker-compose ps
```
---

## Технологический стек

### Backend
- **FastAPI** - современный асинхронный веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **PostgreSQL** - реляционная база данных
- **Alembic** - миграции базы данных
- **Celery + Redis** - асинхронные задачи и очередь
- **Celery Beat** - планировщик периодических задач
- **bcrypt** - хеширование паролей
- **PyJWT** - JWT токены для аутентификации
- **slowapi** - rate limiting

### Frontend
- **Vue 3** - прогрессивный JavaScript фреймворк
- **Vuetify 3** - Material Design компоненты
- **Vite** - сборщик и dev-сервер

### Desktop
- **PyQt6** - кроссплатформенный GUI фреймворк
- **websocket-client** - WebSocket клиент для Python

### DevOps
- **Docker + Docker Compose** - контейнеризация
- **pytest** - тестирование
- **Swagger/ReDoc** - автоматическая документация API

---

## Описание проекта

Сервис позволяет:
- Регистрироваться пользователям через веб-интерфейс
- Получать уникальный ключ активации по email
- Подключаться к прокси-серверу через десктопное приложение
- Отслеживать статус подключения в реальном времени через WebSocket

---

## Основной флоу работы

### 1. Регистрация пользователя

**Через веб-интерфейс:**
1. Открыть http://localhost:5173
2. Перейти на страницу регистрации
3. Ввести email и пароль (минимум 8 символов)
4. Нажать "Зарегистрироваться"

**Что происходит:**
- Создается пользователь в БД
- Генерируется уникальный 32-символьный activation_key
- Celery отправляет задачу на отправку email
- Email выводится в логи celery-worker (console mode)

**Получить ключ активации:**
```bash
docker-compose logs celery-worker | grep -A 10 "EMAIL"
```

Вы увидите:
```
============================================================
[EMAIL] To: user@example.com
Subject: Ключ активации Proxy Gateway

Здравствуйте!

Ваш ключ активации для подключения к прокси-сервису:
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

Если вы не запрашивали этот ключ, просто проигнорируйте письмо.
============================================================
```

### 2. Вход в систему

1. Перейти на страницу входа
2. Ввести email и пароль
3. Получить JWT токен
4. Перейти в личный кабинет

### 3. Просмотр ключа в профиле

В личном кабинете отображается:
- Email пользователя
- Текущий activation_key
- Кнопка "Обновить ключ" (генерирует новый)
- Форма смены пароля

### 4. Подключение через Desktop клиент

**Запуск desktop приложения:**
```bash
cd desktop
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

**Использование:**
1. Вставить activation_key в поле ввода
2. Нажать "Подключиться"
3. Приложение:
   - Отправляет ключ на backend
   - Получает данные свободной VM (host, port, protocol)
   - Подключается к WebSocket для real-time обновлений
   - Отображает статус подключения

**Статусы:**
- `connected` - успешно подключено к прокси
- `disconnected` - отключено
- `no_free_vms` - все прокси заняты
- `error` - ошибка подключения

### 5. Отключение

Нажать кнопку "Отключиться" в desktop приложении или закрыть окно.
VM автоматически освобождается.

---

## API документация

### Swagger UI
http://localhost:8000/docs - интерактивная документация с возможностью тестирования

### ReDoc
http://localhost:8000/redoc - красивая документация в стиле "книги"

### Основные эндпоинты

#### Authentication
```bash
# Регистрация
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "password_confirmation": "password123"
}

# Вход
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
# Возвращает: { "access_token": "...", "token_type": "bearer", "user": {...} }
```

#### Profile (требуется JWT токен)
```bash
# Получить профиль
GET /api/profile
Authorization: Bearer <token>

# Обновить ключ активации
POST /api/profile/refresh-key
Authorization: Bearer <token>

# Сменить пароль
POST /api/profile/change-password
Authorization: Bearer <token>
{
  "current_password": "old_password",
  "new_password": "new_password",
  "new_password_confirmation": "new_password"
}
```

#### Proxy
```bash
# Активировать ключ и получить VM
POST /api/proxy/activate-key
{
  "activation_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
# Возвращает: VM данные + ws_token для WebSocket

# Отключиться от прокси
POST /api/proxy/disconnect
{
  "user_id": 1
}

# Получить статус
GET /api/proxy/status/{user_id}?token=<ws_token>
```

#### WebSocket
```
WS /api/ws/status/{user_id}?token=<ws_token>
```
Real-time обновления статуса подключения.

#### Virtual Machines
```bash
# Список всех VM
GET /api/vms

# Получить VM по ID
GET /api/vms/{vm_id}

# Создать новую VM
POST /api/vms
{
  "name": "proxy-4",
  "host": "192.168.1.104",
  "port": 1080,
  "protocol": "socks5"
}
```

### Rate Limiting

Защита от brute-force атак:
- `/api/auth/register` - 5 запросов/минуту
- `/api/auth/login` - 5 запросов/минуту
- `/api/proxy/activate-key` - 10 запросов/минуту

---

## Структура проекта

```
proxy-gateway/
├── backend/                    # Backend приложение
│   ├── alembic/               # Миграции БД
│   │   └── versions/          # Файлы миграций
│   ├── app/
│   │   ├── api/               # API роуты
│   │   │   └── routes/        # Эндпоинты (auth, profile, proxy, vm, websocket)
│   │   ├── core/              # Ядро приложения
│   │   │   ├── celery_app.py # Конфигурация Celery + Beat
│   │   │   ├── config.py      # Настройки приложения
│   │   │   ├── logging.py     # Логирование
│   │   │   └── rate_limiter.py # Rate limiting
│   │   ├── db/                # База данных
│   │   │   ├── base.py        # Импорты моделей
│   │   │   └── session.py     # Сессии БД
│   │   ├── models/            # SQLAlchemy модели
│   │   │   ├── user.py        # Модель User
│   │   │   └── virtual_machine.py # Модель VirtualMachine
│   │   ├── schemas/           # Pydantic схемы
│   │   │   ├── auth.py        # Схемы аутентификации
│   │   │   ├── proxy.py       # Схемы прокси
│   │   │   ├── user.py        # Схемы пользователя
│   │   │   └── vm.py          # Схемы VM
│   │   ├── services/          # Бизнес-логика
│   │   │   ├── auth.py        # Аутентификация
│   │   │   ├── email.py       # Отправка email
│   │   │   ├── proxy.py       # Управление прокси
│   │   │   ├── security.py    # Хеширование паролей
│   │   │   ├── user.py        # Управление пользователями
│   │   │   └── vm.py          # Управление VM
│   │   ├── tasks/             # Celery задачи
│   │   │   ├── cleanup_tasks.py # Очистка expired данных
│   │   │   └── email_tasks.py   # Отправка email
│   │   └── main.py            # Точка входа FastAPI
│   ├── tests/                 # Тесты (pytest)
│   │   ├── conftest.py        # Фикстуры
│   │   ├── test_auth_and_proxy.py
│   │   ├── test_celery.py
│   │   ├── test_edge_cases.py
│   │   ├── test_login.py
│   │   ├── test_profile.py
│   │   ├── test_proxy.py
│   │   ├── test_rate_limiting.py
│   │   ├── test_registration.py
│   │   ├── test_vm.py
│   │   └── test_websocket.py
│   ├── Dockerfile             # Development образ
│   ├── Dockerfile.prod        # Production образ
│   └── requirements.txt       # Python зависимости
├── frontend/                  # Frontend приложение
│   ├── src/
│   │   ├── components/        # Vue компоненты
│   │   │   └── AuthPanel.vue
│   │   ├── views/             # Страницы
│   │   │   ├── LoginView.vue
│   │   │   ├── ProfileView.vue
│   │   │   └── RegisterView.vue
│   │   ├── services/          # API клиент
│   │   │   └── api.js
│   │   ├── stores/            # State management
│   │   │   └── auth.js
│   │   ├── App.vue            # Главный компонент
│   │   └── main.js            # Точка входа
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── desktop/                   # Desktop приложение
│   ├── app.py                 # PyQt6 приложение
│   └── requirements.txt
├── docker-compose.yml         # Оркестрация контейнеров
├── .env.example               # Пример переменных окружения
└── README.md                  # Этот файл
```

---

## Тестирование

### Запуск тестов

```bash
# Запустить зависимости
docker-compose up -d postgres redis

# Войти в контейнер backend
docker-compose exec backend bash

# Запустить все тесты
pytest

# Запустить с покрытием
pytest --cov=app --cov-report=html

# Запустить конкретный тест
pytest tests/test_proxy.py -v

# Запустить с подробным выводом
pytest -vv
```
---

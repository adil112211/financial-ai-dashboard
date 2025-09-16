# 🏦 Financial AI Dashboard - Казахстанская версия с интеграциями

## 🚀 Полнофункциональная система управления корпоративной ликвидностью

Эта система разработана специально для казахстанских компаний и интегрирована с:
- **Национальным банком РК** (автоматическое получение курсов валют)
- **Мониторингом финансовых новостей** (анализ рисков)
- **AI консультантом** на базе GPT-4
- **n8n автоматизацией** (webhook интеграция)

## ✨ Ключевые возможности

### 📊 **Автоматическая интеграция с НБ РК**
- Ежедневное обновление курсов USD, EUR, RUB к тенге
- Парсинг официального RSS НБ РК
- Хранение исторических данных

### 📰 **Мониторинг финансовых новостей**
- Tengrinews (экономика)
- Forbes Kazakhstan
- Kursiv (бизнес новости)
- Автоматический анализ настроений

### 🤖 **AI анализ и прогнозирование**
- Ежедневные отчеты с анализом рисков
- Персональный AI консультант
- Рекомендации на основе актуальных данных
- Прогнозы влияния новостей на ликвидность

### 🔗 **Интеграция с n8n**
- Webhook endpoints для чат-ботов
- Автоматизация отчетов
- Интеграция с Telegram, Slack, Email
- Настраиваемые workflow'ы

## 🛠 Технологический стек

- **Backend**: FastAPI + Python 3.11
- **База данных**: PostgreSQL 15
- **Кеширование**: Redis
- **AI**: OpenAI GPT-4
- **Автоматизация**: n8n
- **Мониторинг**: Grafana + Prometheus
- **Контейнеризация**: Docker + Docker Compose

## 🚀 Быстрый запуск

### 1. Подготовка

```bash
# Клонируйте или создайте директорию проекта
mkdir financial-ai-dashboard
cd financial-ai-dashboard

# Скопируйте все файлы проекта в эту директорию
```

### 2. Настройка окружения

```bash
# Скопируйте файл конфигурации
cp .env.example .env

# Отредактируйте .env файл:
nano .env
```

**Обязательно настройте:**
- `SECRET_KEY` - секретный ключ для JWT
- `POSTGRES_PASSWORD` - пароль для базы данных
- `OPENAI_API_KEY` - API ключ OpenAI (получите на https://platform.openai.com)
- `N8N_PASSWORD` - пароль для n8n

### 3. Запуск системы

```bash
# Базовый запуск (основные сервисы)
docker compose up -d

# Или полная конфигурация с мониторингом
docker compose --profile monitoring --profile management up -d
```

### 4. Инициализация данных

```bash
# Подождите 2-3 минуты, затем инициализируйте демо данные
curl -X POST "http://localhost:8000/api/init-demo"
```

### 5. Доступ к системе

- **Основное приложение**: http://localhost:8000
- **n8n автоматизация**: http://localhost:5678
- **Grafana мониторинг**: http://localhost:3000 *(если включен)*
- **pgAdmin**: http://localhost:8080 *(если включен)*

**Демо аккаунт:**
- Email: `demo@finai.kz`
- Пароль: `demo123`

## 🔧 Интеграции

### 📈 НБ РК (Автоматическая)

Система автоматически получает курсы валют:
- **Источник**: https://www.nationalbank.kz/rss/get_rates.cfm
- **Частота**: Ежедневно в 08:00 (Алматы)
- **Валюты**: USD, EUR, RUB к KZT
- **Хранение**: PostgreSQL с историей

### 📰 Мониторинг новостей

Источники новостей:
- **Tengrinews**: Экономические новости
- **Forbes Kazakhstan**: Бизнес аналитика  
- **Kursiv**: Финансовые новости
- **Частота**: Каждые 6 часов

### 🤖 AI анализ

- **Модель**: GPT-4
- **Анализ**: Влияние новостей на курсы валют
- **Отчеты**: Ежедневно в 09:00
- **Прогнозы**: Риски и рекомендации

### 🔗 n8n Webhook интеграция

Создайте workflow в n8n с HTTP Request:

```json
{
  "method": "POST",
  "url": "http://finai-app:8000/webhook/n8n/chat",
  "body": {
    "message": "Какая ситуация с курсом доллара?",
    "user_id": "optional_user_id",
    "webhook_url": "http://n8n:5678/webhook/response"
  }
}
```

## 📊 API Endpoints

### Основные
- `GET /` - Веб-интерфейс
- `GET /health` - Статус системы
- `GET /api/dashboard` - Данные дашборда
- `POST /api/auth/login` - Авторизация
- `POST /api/ai/consult` - AI консультация

### n8n Webhooks
- `POST /webhook/n8n/chat` - Чат-бот интеграция
- `GET /webhook/n8n/status` - Статус webhook

### Интеграции
- Автоматическое обновление курсов НБ РК
- Парсинг финансовых новостей
- Генерация AI отчетов

## 🏗 Архитектура

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Web UI        │    │   FastAPI    │    │ PostgreSQL  │
│   (Dashboard)   │◄──►│   Backend    │◄──►│  Database   │
└─────────────────┘    └──────────────┘    └─────────────┘
                              │
                              ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│      n8n        │◄──►│   Webhooks   │    │   Redis     │
│  Automation     │    │  Integration │    │   Cache     │
└─────────────────┘    └──────────────┘    └─────────────┘
                              │
                              ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│  External APIs  │◄──►│  Schedulers  │    │ Monitoring  │
│ (NBK, News, AI) │    │   (Cron)     │    │ (Grafana)   │
└─────────────────┘    └──────────────┘    └─────────────┘
```

## 📋 Примеры использования

### 1. Ежедневный мониторинг ликвидности

Система автоматически:
1. Получает курсы валют из НБ РК
2. Анализирует финансовые новости
3. Генерирует отчет с рекомендациями
4. Отправляет через n8n в Telegram/Email

### 2. AI консультант

```bash
curl -X POST "http://localhost:8000/api/ai/consult" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"question": "Стоит ли сейчас покупать доллары?"}'
```

### 3. Webhook для Telegram бота

Настройте в n8n workflow:
1. Telegram Trigger → получение сообщения
2. HTTP Request → отправка в Financial AI
3. Telegram → отправка ответа пользователю

## 🔒 Безопасность

- JWT аутентификация с долгосрочными токенами
- Шифрование API ключей в базе данных
- CORS настройки для безопасности
- Rate limiting для API endpoints
- Docker контейнеризация

## 📈 Мониторинг

### Grafana Dashboard (опционально)
- Метрики API запросов
- Статистика AI консультаций
- Мониторинг курсов валют
- Анализ новостных трендов

### Логи
- Структурированные логи в JSON
- Ротация логов по размеру
- Отдельные логи для каждого сервиса

## 🛠 Настройка для production

### 1. SSL сертификаты
```bash
# Добавьте SSL сертификаты в ./ssl/
cert.pem
key.pem
```

### 2. Nginx конфигурация
```nginx
# Раскомментируйте HTTPS секцию в nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... остальная конфигурация
}
```

### 3. Резервное копирование
```bash
# Добавьте cron задачу для бэкапов
0 2 * * * docker exec finai-postgres pg_dump -U finai_user finai_db > backup.sql
```

## 🔧 Кастомизация

### Добавление новых источников новостей

Отредактируйте `main.py`, добавьте в `NewsService`:

```python
news_sources = [
    {
        'url': 'https://your-news-source.kz/rss/',
        'source': 'Your Source',
        'category': 'financial'
    }
]
```

### Настройка AI промптов

Модифицируйте `AIAnalysisService.analyze_financial_data()` для изменения стиля анализа.

### Интеграция с банковскими API

Добавьте новые сервисы в `main.py` для интеграции с Open Banking API банков Казахстана.

## 🆘 Troubleshooting

### Проблема: Не получает курсы НБ РК
```bash
# Проверьте логи
docker compose logs finai-app | grep NBK

# Протестируйте API вручную
curl "https://www.nationalbank.kz/rss/get_rates.cfm"
```

### Проблема: AI не отвечает
```bash
# Проверьте API ключ OpenAI
docker compose exec finai-app python -c "import os; print('OPENAI_API_KEY:', os.getenv('OPENAI_API_KEY')[:10])"
```

### Проблема: n8n не подключается
```bash
# Проверьте webhook URL
curl -X GET "http://localhost:8000/webhook/n8n/status"
```

## 📞 Поддержка

- **Email**: support@finai.kz
- **Telegram**: @finai_support
- **Документация**: https://docs.finai.kz
- **Issues**: GitHub Issues

## 📜 Лицензия

MIT License - свободное использование для коммерческих и некоммерческих проектов.

---

## 🎯 Для хакатона

Этот проект идеально подходит для **задачи #2** "Финансовый AI-ассистент":

✅ **Автоматический сбор данных** из НБ РК и новостных источников  
✅ **Отчеты по ликвидности** в реальном времени  
✅ **Сценарии "что если"** через AI консультанта  
✅ **Рекомендации** на основе актуальных курсов и новостей  
✅ **Интеграция с n8n** для автоматизации процессов  

**Готов к демонстрации прямо сейчас!** 🚀
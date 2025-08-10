# 🎂 Birthday Email Notification System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-green.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Celery](https://img.shields.io/badge/Celery-5.5%2B-brightgreen.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-6.4%2B-red.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Pandas](https://img.shields.io/badge/Pandas-2.3%2B-blue.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Love](https://img.shields.io/badge/Made%20with-❤️-ff69b4.svg)](#)
![Made in Ukraine](https://img.shields.io/badge/Made%20in-Ukraine-0057B7.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiPjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iNDAiIHk9IjAiIGZpbGw9IiMwMDU3QjciLz48cmVjdCB3aWR0aD0iMTIwIiBoZWlnaHQ9IjQwIiB5PSI0MCIgZmlsbD0iI0ZGREYwMCIvPjwvc3ZnPg==)

Система автоматичних повідомлень (нагадування) про дні народження співробітників.  
Дозволяє своєчасно інформувати колег та організовувати привітання і збір коштів.

---

## 🚀 Особливості

- ✅ Автоматична розсилка за 2 дні до ДН (в робочі дні)  
- ✅ Смарт-планувальник (пропуск вихідних)  
- ✅ Шаблони з плейсхолдерами `{name}`, `{date}`  
- ✅ Імпорт співробітників з CSV, Excel (.xlsx)  
- ✅ Логування та статистика розсилки  
- ✅ Календар з кольоровим кодуванням  
- ✅ Різні рівні доступу (`admin` / `super_admin`)  
- ✅ Повторні спроби при помилках  

---

## 🛠 Технічний стек

- **Backend:** Flask + SQLAlchemy  
- **Планувальник:** Celery + Redis  
- **База даних:** SQLite3  
- **Email:** Flask-Mail  
- **Авторизація:** Flask-Login  

---

## 🔄 Логіка роботи

### 📅 Розрахунок дати повідомлення
1. Береться дата ДН співробітника.  
2. Віднімається **2 дні**.  
3. Якщо дата припадає на вихідний — переноситься на останній робочий день.

### 🕒 Щоденна перевірка
1. **Celery Beat** запускає задачу в зазначений у файлі `.env` час.  
2. Перевіряє, чи сьогодні робочий день.  
3. Шукає співробітників, про ДН яких сьогодні треба відправити нагадування.  
4. Отримує активний шаблон (тіло листа з плейсхолдерами).  
5. Відправляє email усім співробітникам **(крім іменинника)**.  
6. Логує результат у системі.

### ⚠ Обробка помилок
- Автоматичні повторні спроби.  
- Затримка між спробами.  
- Детальне логування помилок.  
- Збереження статусу в БД (`sent` / `failed` / `retry`).  

---

## 📦 Встановлення та запуск

### 🔹 Без Docker

#### 1. Клонування репозиторію
```bash
git clone https://github.com/sergbondckua/birthday_email_notification_system.git
cd birthday_email_notification_system
```

#### 2. Створення та активація віртуального середовища
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
```

#### 3. Інсталювання залежностей
```bash
pip install -r requirements.txt
```

#### 4. Створення файлу `.env`
```bash
cp env_dist .env
nano .env  # Linux/MacOS
notepad .env  # Windows
```

#### 5. Запуск сервісу
```bash
python app.py
```

##### Запуск Redis
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

##### Запуск Celery
```bash
celery -A celery_worker.celery worker --loglevel=info
celery -A celery_worker.celery beat --loglevel=info
celery -A celery_worker.celery flower
```

#### 6. Ініціалізація бази даних та створення superuser
```bash
flask --app manage.py init-db
flask --app manage.py createsuperuser
```

---

### 🔹 Docker
```bash
docker compose up --build -d

# Додавання superuser
docker exec -it bdaygo_web bash
flask --app manage.py init-db
flask --app manage.py createsuperuser
```



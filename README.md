# ml-big-data

Веб-приложение для загрузки CSV-файлов, выбора целевой переменной и автоматического обучения модели регрессии. Предоставляет визуализацию статистики данных и метрики качества модели.

## Требования

- Docker
- Docker Compose

## Как запустить

### 1. Клонирование репозитория 

```bash
$ git clone https://github.com/olmaximova/ml-big-data.git
$ cd ml-big-data
```

### 2. Запуск приложения
```bash
docker compose up --build
```

Приложение будет доступно по адресу: http://127.0.0.1:8000/
Swagger будет доступен по адресу: http://127.0.0.1:8000/docs

## Стек
- **Backend:** Python, FastAPI, SQLAlchemy, asyncpg, scikit-learn, pandas, pydantic
- **Database:** PostgreSQL 17
- **Frontend:** HTML, CSS, JavaScript (Vanilla), Chart.js
- **Инфраструктура:** Docker, Docker Compose
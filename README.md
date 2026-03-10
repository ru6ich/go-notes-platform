# Go Notes Platform

Учебный DevOps/SRE-проект, в котором простой сервис заметок постепенно обрастает инфраструктурой: PostgreSQL, reverse proxy на nginx, контейнеризация, Docker Compose, а далее — Kubernetes, k8s troubleshooting и CI/CD.

## Текущее состояние проекта

На текущем этапе в проекте уже реализованы:

- Go API
- PostgreSQL
- nginx reverse proxy
- Python reporter
- Dockerfile для API и reporter
- запуск всего стека через Docker Compose
- healthcheck-зависимости между сервисами

## Архитектура

Текущая схема работы:

```text
client -> localhost:8081 -> nginx:80 -> api:8080 -> postgres:5432
                               ^
                               |
                        reporter -> http://nginx/healthz
```

- с хоста пользователь обращается на `localhost:8081`
- внутри контейнера nginx слушает `80`
- nginx проксирует запросы на `api:8080`
- Go API работает на `8080`
- PostgreSQL работает на `5432`

## Компоненты

### Go API

Основной backend-сервис приложения.

Что делает:

- отдает `GET /healthz`
- отдает `GET /notes`
- принимает `POST /notes`
- работает с PostgreSQL

### PostgreSQL

База данных проекта.

Используется для хранения:

- заметок (`notes`)
- результатов проверок reporter (`api_checks`)

Инициализация выполняется через `db/init.sql`.

### nginx

Reverse proxy перед Go API.

Что делает:

- принимает внешний трафик на `localhost:8081`
- слушает `80` внутри контейнера
- проксирует запросы в `api:8080`

### Python reporter

Сервис технических проверок и генерации отчётов.

Что делает:

- периодически ходит в `http://nginx/healthz`
- измеряет latency и success/fail
- пишет результаты в PostgreSQL
- сохраняет отчёты в `reporter/reports`

## Артефакты reporter

После работы reporter в каталоге `reporter/reports` могут появляться:

- `summary.csv`
- `latency.png`
- `success_rate.png`
- `stats.json`

## Стек

- Go
- Python
- PostgreSQL
- nginx
- Docker
- Docker Compose

Следующие этапы лабораторной:

- Kubernetes
- Kubernetes troubleshooting
- CI/CD

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ru6ich/go-notes-platform.git
cd go-notes-platform
```

### 2. Поднять проект

```bash
docker compose up --build
```

### 3. Проверить статус контейнеров

```bash
docker compose ps
```

## Проверка работы

### Healthcheck через nginx

```bash
curl http://localhost:8081/healthz
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

### Получить список заметок

```bash
curl http://localhost:8081/notes
```

### Создать заметку

```bash
curl -X POST http://localhost:8081/notes \
  -H "Content-Type: application/json" \
  -d '{"text":"first note"}'
```

## Сервисы Docker Compose

### postgres

- образ: `postgres:17`
- хранит данные приложения
- использует volume `postgres_data`
- инициализируется через `db/init.sql`

### api

- собирается из `Dockerfile.api`
- работает на внутреннем порту `8080`
- зависит от `postgres`
- имеет healthcheck по `http://localhost:8080/healthz`

### nginx

- использует образ `nginx:1.27`
- зависит от готовности `api`
- публикует порт `8081:80`
- использует конфиг `nginx/nginx.conf`

### reporter

- собирается из `Dockerfile.reporter`
- использует `TARGET_URL=http://nginx/healthz`
- зависит от `postgres`, `api` и `nginx`
- сохраняет артефакты в `reporter/reports`

## Полезные команды

### Все логи

```bash
docker compose logs -f
```

### Логи отдельных сервисов

```bash
docker compose logs -f postgres
docker compose logs -f api
docker compose logs -f nginx
docker compose logs -f reporter
```

### Остановить проект

```bash
docker compose down
```

### Остановить проект с удалением volume

```bash
docker compose down -v
```

## Переменные окружения

Пример доступных переменных есть в `.env.example`:

- `APP_PORT`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `TARGET_URL`
- `CHECK_INTERVAL_SECONDS`
- `REPORT_EVERY_N_CHECKS`

## Структура проекта

```text
.
├── api/
│   ├── cmd/
│   └── internal/
├── db/
│   └── init.sql
├── docs/
│   ├── architecture.md
│   ├── lab-notes.md
│   └── troubleshooting.md
├── nginx/
│   └── nginx.conf
├── reporter/
│   ├── reporter.py
│   ├── requirements.txt
│   └── reports/
├── Dockerfile.api
├── Dockerfile.reporter
├── compose.yaml
└── README.md
```

## Что уже закрыто в лабораторной

Уже завершены этапы:

- базовое приложение на Go
- Python reporter
- подключение PostgreSQL
- nginx reverse proxy
- контейнеризация сервисов
- запуск через Docker Compose
- базовая отладка контейнерного стенда

## Что дальше

Следующий инфраструктурный этап — перенос текущего Compose-стека в Kubernetes:

- PostgreSQL
- Go API
- nginx
- reporter
- конфигурация
- healthchecks
- сетевое взаимодействие

После этого можно переходить к k8s troubleshooting и затем к CI/CD.

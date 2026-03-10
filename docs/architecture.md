# Architecture

## Overview

`go-notes-platform` — учебный многосервисный проект вокруг простого приложения для заметок.
На текущем этапе система запускается через Docker Compose и включает четыре основных компонента:

- PostgreSQL
- Go API
- nginx reverse proxy
- Python reporter

## Current architecture

```text
client
  |
  v
localhost:8081
  |
  v
nginx:80
  |
  v
api:8080
  |
  v
postgres:5432

reporter
  |
  v
http://nginx/healthz
```

## Main idea

Архитектура специально сделана не одноконтейнерной, а многосервисной, чтобы отработать типичные DevOps/SRE-сценарии:

- backend зависит от базы данных
- внешний доступ идет через reverse proxy
- отдельный сервис выполняет технические проверки приложения
- сервисы связаны общей compose-сетью и зависимостями по healthcheck

Это делает проект хорошей промежуточной стадией перед Kubernetes.

---

## Components

### 1. PostgreSQL

**Назначение:** хранение данных приложения.

**Используется для:**

- таблицы `notes`
- таблицы `api_checks`

**Особенности:**

- образ `postgres:17`
- volume `postgres_data`
- инициализация через `db/init.sql`
- healthcheck через `pg_isready`

**Почему важно:**

PostgreSQL добавляет в проект stateful-компонент и позволяет практиковать:

- volumes
- init-скрипты
- подключение приложения к БД
- диагностику проблем между сервисом и базой

---

### 2. Go API

**Назначение:** основной backend-сервис.

**Функции:**

- `GET /healthz`
- `GET /notes`
- `POST /notes`

**Особенности:**

- запускается в отдельном контейнере
- слушает внутренний порт `8080`
- зависит от готовности PostgreSQL
- имеет собственный healthcheck

**Почему важно:**

Go API — центральный сервис системы. На нем удобно тренировать:

- работу с environment variables
- сетевое взаимодействие контейнеров
- healthcheck/readiness-логику
- диагностику соединения с БД

---

### 3. nginx

**Назначение:** reverse proxy перед Go API.

**Функции:**

- принимает внешний трафик
- выступает единой точкой входа
- проксирует запросы в `api:8080`

**Особенности:**

- внутри контейнера слушает порт `80`
- наружу опубликован как `localhost:8081`
- использует `nginx/nginx.conf`
- стартует после готовности API

**Почему важно:**

Наличие nginx приближает проект к реальной эксплуатационной схеме и позволяет практиковать:

- proxy-конфигурацию
- различие host и container ports
- диагностику проблем маршрутизации
- подготовку к будущему переходу на Service/Ingress в Kubernetes

---

### 4. Python reporter

**Назначение:** сервис технического мониторинга и отчетности.

**Функции:**

- периодически проверяет `http://nginx/healthz`
- измеряет latency
- фиксирует success/fail
- сохраняет результаты в БД
- генерирует отчеты

**Артефакты:**

- `summary.csv`
- `latency.png`
- `success_rate.png`
- `stats.json`

**Почему важно:**

Reporter добавляет в проект operational-составляющую:

- периодические проверки
- метрики доступности на базовом уровне
- отдельный служебный контейнер
- сценарии диагностики цепочки `nginx -> api`

---

## Network model

Все сервисы работают в одной Docker Compose-сети и обращаются друг к другу по service name:

- `postgres`
- `api`
- `nginx`
- `reporter`

Это означает:

- API подключается к БД по имени `postgres`
- nginx проксирует на `api`
- reporter ходит на `nginx`

### Important port distinction

Нужно четко разделять внешние и внутренние порты:

- host: `localhost:8081`
- nginx container: `80`
- api container: `8080`
- postgres container: `5432`

Именно поэтому пользователь с машины обращается на `8081`, хотя внутри контейнерной сети nginx продолжает работать на `80`.

---

## Startup order

Текущий compose-стек использует зависимости по состоянию сервисов:

1. Сначала поднимается `postgres`
2. После его healthcheck стартует `api`
3. После готовности API стартует `nginx`
4. Reporter начинает проверки после старта инфраструктуры

Такой порядок помогает избежать типичных проблем:

- API стартует раньше базы
- nginx проксирует в неготовый backend
- reporter начинает проверки до старта приложения

---

## Data flows

### User request flow

```text
client -> localhost:8081 -> nginx -> api -> postgres
```

### Healthcheck flow

```text
reporter -> nginx/healthz -> api/healthz -> database record + reports
```

---

## Configuration sources

Основная конфигурация на текущем этапе задается через:

- `compose.yaml`
- `.env.example`
- `nginx/nginx.conf`
- `db/init.sql`

Это удобно для лабораторной, потому что позволяет явно видеть:

- какие параметры нужны каждому сервису
- как сервисы связаны между собой
- что потом можно будет вынести в ConfigMap и Secret

---

## Why this architecture is useful before Kubernetes

Текущая Compose-архитектура уже естественно раскладывается на будущие k8s-объекты:

- `postgres` -> stateful workload + persistent storage
- `api` -> deployment + service
- `nginx` -> deployment + service
- `reporter` -> deployment или отдельный worker
- env vars -> ConfigMap / Secret
- healthchecks -> probes

То есть текущая стадия — это удобный мост между локальной контейнерной сборкой и полноценной оркестрацией в Kubernetes.

## Next step

Следующий инфраструктурный этап — перенос текущего стека в Kubernetes с сохранением той же логики:

- отдельные workload-объекты
- конфигурация через ConfigMap и Secret
- persistent storage для PostgreSQL
- сервисы для сетевого взаимодействия
- последующий k8s troubleshooting
- затем CI/CD

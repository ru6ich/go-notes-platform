# Lab Notes

## Текущая стадия

На данный момент в лабораторной уже завершены:

- Go API
- Python reporter
- PostgreSQL
- nginx reverse proxy
- Dockerfile для сервисов
- Docker Compose
- базовая проверка и troubleshooting контейнерного стенда

## Зафиксированная рабочая схема

```text
client -> localhost:8081 -> nginx:80 -> api:8080 -> postgres:5432
                               ^
                               |
                        reporter -> http://nginx/healthz
```

## Что важно помнить

- внешний вход идет через `localhost:8081`
- nginx внутри контейнера слушает `80`
- API внутри контейнера работает на `8080`
- reporter проверяет приложение не напрямую, а через nginx
- таблицы создаются через `db/init.sql`

## Следующие этапы

1. Kubernetes
2. Kubernetes troubleshooting
3. CI/CD

## Смысл следующего шага

Теперь задача — перенести уже рабочую Compose-архитектуру в Kubernetes, не меняя саму логику приложения:

- база данных
- API
- reverse proxy
- reporter
- конфигурация
- healthchecks
- сетевое взаимодействие

# Go Notes Platform

Учебная лабораторная по DevOps/SRE-практике.

## Архитектура

client -> nginx -> go-api -> postgres
                  ^
                  |
             python-reporter

## Стек
- Go
- Python
- PostgreSQL
- nginx
- Docker
- Docker Compose
- Kubernetes

## План
1. Реализовать Go API
2. Реализовать Python reporter
3. Добавить Postgres
4. Добавить nginx reverse proxy
5. Контейнеризировать всё
6. Поднять через Docker Compose
7. Перенести в Kubernetes

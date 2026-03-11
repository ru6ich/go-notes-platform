# Docker / Docker Compose Cheatsheet

Короткая практическая шпаргалка для сборки, запуска и диагностики контейнеров.

---

## Базовая логика диагностики

Запомнить как цепочку:

**смотрю → читаю → захожу → проверяю сеть → проверяю конфиг**

- `ps` — какие контейнеры вообще живы
- `logs` — что пишет приложение
- `exec` — что внутри контейнера
- `inspect` / `port` / `network` — как контейнер связан снаружи и с другими
- `compose config` — что реально получилось из compose-файла

---

## Docker: самые нужные команды

### Посмотреть контейнеры

```bash
docker ps
docker ps -a
docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'
```

### Посмотреть логи

```bash
docker logs <container-name>
docker logs -f <container-name>
docker logs --tail=50 <container-name>
```

### Зайти внутрь контейнера

```bash
docker exec -it <container-name> sh
docker exec -it <container-name> bash
docker exec <container-name> env
```

### Посмотреть порты

```bash
docker port <container-name>
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

### Посмотреть подробности контейнера

```bash
docker inspect <container-name>
docker inspect <container-name> --format '{{json .NetworkSettings.Ports}}'
```

### Посмотреть образы

```bash
docker images
docker image ls
```

### Сборка образа

```bash
docker build -t my-app:local .
docker build -t go-notes-api:local -f Dockerfile.api .
docker build -t go-notes-reporter:local -f Dockerfile.reporter .
```

### Удалить контейнер / образ

```bash
docker stop <container-name>
docker rm <container-name>
docker rmi <image-name>
```

---

## Docker Compose: самые нужные команды

### Поднять проект

```bash
docker compose up
docker compose up -d
docker compose up --build
```

### Остановить проект

```bash
docker compose down
docker compose down -v
```

### Посмотреть состояние

```bash
docker compose ps
docker compose top
```

### Посмотреть логи

```bash
docker compose logs
docker compose logs -f
docker compose logs -f api
docker compose logs -f nginx
docker compose logs -f postgres
docker compose logs -f reporter
```

### Пересобрать сервис

```bash
docker compose build
docker compose build api
docker compose up -d --build api
```

### Выполнить команду внутри сервиса

```bash
docker compose exec api sh
docker compose exec postgres psql -U notesuser -d notesdb
docker compose exec reporter ls -la /app/reports
```

### Посмотреть итоговый compose-конфиг

```bash
docker compose config
```

---

## Полезные сетевые команды

### Кто занимает порт на хосте

```bash
ss -ltnp | grep 8081
sudo ss -ltnp | grep 8081
sudo lsof -iTCP:8081 -sTCP:LISTEN -P -n
```

### Найти контейнер по опубликованному порту

```bash
docker ps --filter publish=8081 --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Ports}}'
```

### Посмотреть docker networks

```bash
docker network ls
docker network inspect <network-name>
```

---

## Быстрые сценарии диагностики

### Если контейнер не стартует

```bash
docker ps -a
docker logs <container-name>
docker inspect <container-name>
```

### Если сервис поднят, но не отвечает снаружи

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}'
ss -ltnp | grep <host-port>
curl http://localhost:<host-port>
```

### Если nginx не достаёт API

```bash
docker compose logs -f nginx
docker compose logs -f api
docker compose exec nginx sh
```

### Если приложение не достаёт БД

```bash
docker compose logs -f api
docker compose logs -f postgres
docker compose exec postgres psql -U notesuser -d notesdb
```

### Если volume ведёт себя странно

```bash
docker volume ls
docker volume inspect <volume-name>
docker compose down -v
```

---

## Самое важное по понятиям

- `image` — шаблон контейнера
- `container` — запущенный экземпляр image
- `Dockerfile` — инструкция, как собрать image
- `volume` — постоянные данные
- `network` — сеть между контейнерами
- `compose service` — описание одного сервиса в compose.yaml
- `ports` — проброс `host:container`
- `env` — переменные окружения

---

## Минимальный набор наизусть

```bash
docker ps
docker logs
docker exec
docker inspect
docker compose ps
docker compose logs
docker compose up -d
docker compose down
```

## Сценарий 1: неверный DB_HOST у API

Симптом:
- `api` не становится healthy
- `nginx` отдает `502 Bad Gateway`
- пользовательские ручки недоступны

Диагностика:
- `docker compose ps`
- `docker compose logs api --tail 50`
- `curl http://localhost:8081/healthz`

Что показала диагностика:
- в логах `api` ошибка:
  `lookup postgres-broken on 127.0.0.11:53: no such host`

Причина:
- у сервиса `api` в `compose.yaml` был указан неверный `DB_HOST`

Исправление:
- вернуть `DB_HOST: postgres`
- выполнить `docker compose up -d --force-recreate api reporter`

## Сценарий 2: неверный upstream-порт в nginx

### Симптом

- `GET /healthz` и `GET /notes` через `localhost:8081` возвращали `502 Bad Gateway`
- `docker compose ps` показывал, что:
  - `api` — `healthy`
  - `postgres` — `healthy`
  - `nginx` — `Up`
  - `reporter` — `Up`

### Диагностика

Проверил:
```bash
curl -i http://localhost:8081/healthz
curl -i http://localhost:8081/notes
docker compose logs nginx --tail 50
docker compose logs api --tail 50
```
В логах nginx была ключевая ошибка:
`upstream: "http://172.18.0.3:9999/healthz"`

Что это означало?

* `nginx` успешно резолвил `upstream` и пытался подключиться к `api`
* проблема была не в `DNS` и не в имени сервиса
* ошибка `connection refused` означала, что адрес найден, но на указанном порту никто не слушает
* `api` при этом был жив и продолжал обслуживать `/healthz`

### Первопричина
В nginx/nginx.conf был указан неверный proxy_pass:
`proxy_pass http://api:9999;`
 вместо верного
`proxy_pass http://api:8080;`

### Исправление
Исправить proxy_pass в nginx/nginx.conf:
`proxy_pass http://api:8080;`
Затем перезапустить nginx:
`docker compose restart nginx`

### Проверка после исправления:
```bash
curl -i http://localhost:8081/healthz
curl -i http://localhost:8081/notes
docker compose ps
```
Ожидаемый результат:
* `GET /healthz` возвращает `200 OK`
* `GET /notes` возвращает `200 OK`
* `nginx` продолжает работать без `502`

### Вывод:
Если nginx отдает 502 Bad Gateway, а api при этом healthy, нужно в первую очередь смотреть:
* логи nginx
* строку upstream

тип ошибки:
* host not found — проблема с именем
* connection refused — проблема с портом или процессом на этом порту 


## Сценарий 3: неверный healthcheck у API

### Симптом
- `docker compose ps` показывает `api` как `unhealthy`
- при этом `GET /healthz` и `GET /notes` через `nginx` работают нормально

### Диагностика
Проверил:
- `curl http://localhost:8081/healthz`
- `curl http://localhost:8081/notes`
- `docker compose ps`
- `docker inspect go-notes-api-compose --format '{{json .State.Health}}'`

Health log показал:
`curl: (7) Failed to connect to localhost port 8088`

### Причина
В `compose.yaml` healthcheck API был настроен на неверный порт `8088` вместо `8080`.

### Исправление
- вернуть:
  `test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]`
- выполнить:
  `docker compose up -d --force-recreate api`

### Вывод
Приложение может быть рабочим, а контейнер — unhealthy, если неправильно настроен healthcheck.


## Сценарий k8s-1: broken selector on `Service api`

### Goal

Научиться диагностировать ситуацию, когда Pod жив, а приложение не работает из-за неправильной связи между `Service` и Pod.

### Failure

У `Service api` selector был изменён с:

```yaml
selector:
  app: api
```

на:

```yaml
selector:
  app: api-broken
```

### Symptoms

- `curl http://localhost:8081/healthz` перестаёт работать через nginx
- `curl http://localhost:8081/notes` перестаёт работать
- `api` Pod остаётся `Running`
- `nginx` может стать `0/1` и начать рестартиться
- `nginx` не может подключиться к upstream API

### Diagnostic commands

```bash
kubectl -n go-notes-platform get pods
kubectl -n go-notes-platform get svc
kubectl -n go-notes-platform get endpoints
kubectl -n go-notes-platform describe svc api
kubectl -n go-notes-platform describe svc nginx
kubectl -n go-notes-platform logs deploy/nginx --tail=50
kubectl -n go-notes-platform logs deploy/api --tail=50
kubectl -n go-notes-platform get pod --show-labels
kubectl -n go-notes-platform get svc api -o yaml
```

### What to notice

- `api` Pod жив и healthy
- `Service api` существует
- endpoints у `api` отсутствуют или не совпадают с ожидаемыми
- selector у `Service api` не совпадает с label Pod’а
- в логах nginx видны ошибки подключения к upstream

Пример симптома в логах nginx:

```text
connect() failed (111: Connection refused) while connecting to upstream
```

### Root cause

`Service api` не выбирает Pod API из-за неправильного selector.

### Fix via patch

```bash
kubectl -n go-notes-platform patch service api   --type='merge'   -p '{"spec":{"selector":{"app":"api"}}}'
```

### Fix via manifest

Открыть файл:

```text
k8s/03-api.yaml
```

Убедиться, что selector сервиса выглядит так:

```yaml
spec:
  selector:
    app: api
```

Потом применить заново:

```bash
kubectl apply -f k8s/03-api.yaml
```

### Validation after fix

```bash
kubectl -n go-notes-platform get endpoints api
kubectl -n go-notes-platform get pods
kubectl -n go-notes-platform port-forward svc/nginx 8081:80
```

In another terminal:

```bash
curl http://localhost:8081/healthz
curl http://localhost:8081/notes
```

### Main lesson

`Pod` и `Deployment` могут быть полностью живыми, но приложение всё равно не работает, если `Service` смотрит не на те labels.

---

## Notes

Следующие полезные blind troubleshooting-сценарии для практики:

- сломанный `TARGET_URL` у reporter
- неправильный `DB_PASSWORD`
- сломанный selector у `Service nginx`
- удаление PVC и последствия для stateful сервиса
- поломка readiness probe

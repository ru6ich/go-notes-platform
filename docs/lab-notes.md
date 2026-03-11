# Lab notes

## Project

`go-notes-platform` — учебная DevOps/SRE лабораторная по постепенному развитию многосервисного приложения.

## Current stage

На текущем этапе проект уже перенесён с Docker Compose в Kubernetes и полностью работает в локальном Minikube-кластере.

## What is already done

### Container stage

Завершено:

- Dockerfile для Go API
- Dockerfile для Python reporter
- multi-stage build для API
- базовый runtime-образ для сервисов

### Reverse proxy stage

Завершено:

- отдельный nginx как точка входа
- проксирование запросов в Go API
- схема `localhost:8081 -> nginx -> api`

### Docker Compose stage

Завершено:

- `postgres`
- `api`
- `nginx`
- `reporter`
- volumes
- env-конфигурация
- init SQL
- compose-запуск и базовая диагностика

### Kubernetes stage

Завершено:

- запуск локального кластера Minikube
- `Namespace`
- `ConfigMap`
- `Secret`
- `StatefulSet` для PostgreSQL
- `PVC` для PostgreSQL
- `Deployment + Service` для API
- `Deployment + Service` для nginx
- `Deployment + PVC` для reporter
- проверка доступа через `kubectl port-forward svc/nginx 8081:80`

## Implemented Kubernetes resources

### `k8s/00-namespace.yaml`

- namespace `go-notes-platform`

### `k8s/01-config.yaml`

- `ConfigMap app-config`
- `Secret app-secret`

### `k8s/02-postgres.yaml`

- `ConfigMap postgres-init-sql`
- `Service postgres`
- `StatefulSet postgres`
- `volumeClaimTemplates` для данных БД

### `k8s/03-api.yaml`

- `Service api`
- `Deployment api`
- init container ожидания Postgres
- readiness/liveness probes

### `k8s/04-nginx.yaml`

- `ConfigMap nginx-config`
- `Service nginx`
- `Deployment nginx`
- init container ожидания API
- readiness/liveness probes

### `k8s/05-reporter.yaml`

- `PVC reporter-reports`
- `Deployment reporter`
- init containers ожидания Postgres и nginx

## What was verified manually

Проверено руками:

- `postgres` успешно инициализируется и применяет `init.sql`
- API отвечает на `/healthz` и `/notes`
- nginx проксирует запросы к API
- reporter выполняет циклические проверки `http://nginx/healthz`
- reporter пишет результаты в БД
- reporter генерирует:
  - `summary.csv`
  - `latency.png`
  - `success_rate.png`
  - `stats.json`

## First blind troubleshooting scenario

Проведён первый blind troubleshooting-сценарий в Kubernetes.

### Scenario

Сломан selector у `Service api`.

### Symptoms

- `curl` через nginx перестал работать
- `nginx` начал падать по probes
- `api` Pod оставался живым
- `Service api` существовал, но не имел корректных endpoints

### Key conclusion

Даже если Pod и Deployment живы, приложение всё равно может не работать, если `Service` смотрит не на те labels.

## Current result

На текущий момент весь стек работает в Kubernetes:

- `postgres-0` -> `Running`
- `api` -> `Running`
- `nginx` -> `Running`
- `reporter` -> `Running`

## Next step

Следующий этап:

- дополнительные blind troubleshooting-сценарии в Kubernetes
- полировка манифестов
- подготовка CI/CD

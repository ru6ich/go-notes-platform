# Lab notes

## Project

`go-notes-platform` — учебная DevOps/SRE лабораторная по постепенному развитию многосервисного приложения.

## Current stage

На текущем этапе проект уже перенесён с Docker Compose в Kubernetes, получил CI в GitHub Actions, публикацию образов в GHCR и ручной deploy конкретного SHA в локальный кластер.

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

### Kubernetes troubleshooting stage

Завершено:

- первый blind troubleshooting-сценарий
- поломка selector у `Service api`
- диагностика через `get`, `describe`, `logs`, `endpoints`, `labels`
- восстановление корректного selector

### CI stage

Завершено:

- первый GitHub Actions workflow
- проверка Go API
- проверка Python reporter
- проверка Docker build для обоих сервисов
- обновление setup actions до актуальных версий

### Image delivery stage

Завершено:

- публикация Docker-образов в GHCR
- теги `latest` и `<commit-sha>`
- проверка появления packages в GitHub

### Manual deploy by SHA stage

Завершено:

- rollout образов из GHCR в Kubernetes
- ручное обновление `api` и `reporter`
- проверка rollout status
- фиксация SHA-образов в k8s-манифестах

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
- image из GHCR по конкретному SHA

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
- image из GHCR по конкретному SHA

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
- образы успешно публикуются в GHCR
- Kubernetes успешно тянет образы из GHCR
- deploy по SHA завершает rollout

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

Дополнительно:

- CI workflow успешен
- образы публикуются в GHCR
- deploy по SHA работает вручную

## Next step

Следующий этап:

- дополнительные blind troubleshooting-сценарии в Kubernetes
- усиление CI
- валидация k8s-манифестов
- возможные следующие шаги по CD без self-hosted runner

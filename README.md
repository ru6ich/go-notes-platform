# go-notes-platform

Учебный Go / DevOps / SRE-проект вокруг простого сервиса заметок.

Проект начинался как локальный стенд на Docker Compose, а затем был перенесён в Kubernetes. В репозитории собраны backend на Go, PostgreSQL, `nginx` как reverse proxy, Python reporter, Kubernetes-манифесты, CI в GitHub Actions и публикация Docker-образов в GHCR.

## Что реализовано

На текущем этапе в проекте есть:

- Go API
- PostgreSQL
- `nginx` reverse proxy
- Python reporter
- Dockerfile для API и reporter
- запуск стека через Docker Compose
- перенос стека в Kubernetes
- blind troubleshooting-сценарии в Kubernetes
- GitHub Actions CI
- публикация образов в GHCR
- ручной deploy конкретного SHA в Kubernetes

## Архитектура

### Этап Docker Compose

```text
client -> localhost:8081 -> nginx:80 -> api:8080 -> postgres:5432
                               ^
                               |
                        reporter -> http://nginx/healthz
```

### Этап Kubernetes

```text
client -> kubectl port-forward svc/nginx 8081:80
                    |
                    v
               Service/nginx
                    |
                    v
                 Pod/nginx
                    |
                    v
                 Service/api
                    |
                    v
                  Pod/api
                    |
                    v
              Service/postgres
                    |
                    v
               Pod/postgres-0

reporter Pod -> http://nginx/healthz
```

## Kubernetes-ресурсы

Текущая архитектура в Kubernetes разложена так:

- `postgres` -> `StatefulSet + Service + PVC`
- `api` -> `Deployment + Service`
- `nginx` -> `Deployment + Service`
- `reporter` -> `Deployment + PVC`
- общие env-переменные -> `ConfigMap`
- пароль БД -> `Secret`

## Структура репозитория

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── api/
├── db/
│   └── init.sql
├── docs/
│   ├── architecture.md
│   ├── lab-notes.md
│   ├── troubleshooting.md
│   ├── cicd-notes.md
│   └── cheatsheets/
│       ├── kubernetes-cheatsheet.md
│       └── docker-compose-cheatsheet.md
├── k8s/
│   ├── 00-namespace.yaml
│   ├── 01-config.yaml
│   ├── 02-postgres.yaml
│   ├── 03-api.yaml
│   ├── 04-nginx.yaml
│   └── 05-reporter.yaml
├── nginx/
│   └── nginx.conf
├── reporter/
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile.api
├── Dockerfile.reporter
├── compose.yaml
└── README.md
```

## Быстрый старт через Docker Compose

### Запуск

```bash
docker compose up --build
```

### Проверка

```bash
docker compose ps
docker compose logs -f
curl http://localhost:8081/healthz
curl http://localhost:8081/notes
```

### Остановка

```bash
docker compose down
```

## Запуск в Kubernetes

Ниже пример локального запуска через Minikube.

### 1. Запустить Minikube

```bash
minikube start --driver=docker
kubectl config current-context
kubectl get nodes
```

### 2. Собрать локальные образы внутри Minikube

```bash
eval $(minikube -p minikube docker-env)

docker build -t go-notes-api:local -f Dockerfile.api .
docker build -t go-notes-reporter:local -f Dockerfile.reporter .
```

### 3. Применить манифесты

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-config.yaml
kubectl apply -f k8s/02-postgres.yaml
kubectl apply -f k8s/03-api.yaml
kubectl apply -f k8s/04-nginx.yaml
kubectl apply -f k8s/05-reporter.yaml
```

### 4. Проверить объекты в кластере

```bash
kubectl -n go-notes-platform get all,pvc
```

### 5. Открыть приложение

```bash
kubectl -n go-notes-platform port-forward svc/nginx 8081:80
```

В другом терминале:

```bash
curl http://localhost:8081/healthz
curl http://localhost:8081/notes
```

## CI/CD

### CI

В репозитории настроен GitHub Actions workflow, который:

- запускается на `push`
- запускается на `pull_request`
- вручную запускается через `workflow_dispatch`

Workflow проверяет:

- Go API (`go test` и `go build`)
- Python reporter
- сборку Docker-образа API
- сборку Docker-образа reporter

### Публикация образов

После успешного CI workflow публикует Docker-образы в GHCR.

Используются образы вида:

- `ghcr.io/ru6ich/go-notes-api:latest`
- `ghcr.io/ru6ich/go-notes-api:<commit-sha>`
- `ghcr.io/ru6ich/go-notes-reporter:latest`
- `ghcr.io/ru6ich/go-notes-reporter:<commit-sha>`

### Ручной deploy по SHA

Для деплоя в Kubernetes используется ручной rollout по конкретному SHA.

Пример:

```bash
kubectl -n go-notes-platform set image deployment/api \
  api=ghcr.io/ru6ich/go-notes-api:<SHA>

kubectl -n go-notes-platform set image deployment/reporter \
  reporter=ghcr.io/ru6ich/go-notes-reporter:<SHA>

kubectl -n go-notes-platform rollout status deployment/api
kubectl -n go-notes-platform rollout status deployment/reporter
```

После успешного rollout используемый SHA фиксируется в `k8s/03-api.yaml` и `k8s/05-reporter.yaml`, чтобы source of truth снова оставался в манифестах.

## Reporter outputs

Reporter сохраняет отчёты в `/app/reports`.

Ожидаемые файлы:

- `summary.csv`
- `latency.png`
- `success_rate.png`
- `stats.json`

Проверка в Kubernetes:

```bash
kubectl -n go-notes-platform exec deploy/reporter -- ls -la /app/reports
kubectl -n go-notes-platform exec deploy/reporter -- cat /app/reports/stats.json
```

## Полезные команды Kubernetes

```bash
kubectl -n go-notes-platform get pods,svc,endpoints,pvc
kubectl -n go-notes-platform describe pod <pod-name>
kubectl -n go-notes-platform logs deploy/<deployment-name>
kubectl -n go-notes-platform exec -it <pod-name> -- sh
kubectl -n go-notes-platform port-forward svc/<service-name> 8081:80
```

## Прогресс по этапам

### Уже сделано

- Dockerfile для API и reporter
- `nginx` reverse proxy
- orchestration через Docker Compose
- troubleshooting в Compose
- Kubernetes namespace / config / secret
- PostgreSQL в Kubernetes
- API в Kubernetes
- `nginx` в Kubernetes
- reporter в Kubernetes
- первый blind troubleshooting-сценарий в Kubernetes
- GitHub Actions CI
- публикация образов в GHCR
- ручной deploy по SHA

### Что можно развивать дальше

- новые Kubernetes troubleshooting-сценарии
- валидация Kubernetes-манифестов в CI
- linting и более строгие проверки
- частичная или полная автоматизация deploy

## Что показывает этот проект

Главная цель проекта — не просто поднять стек, а на практике разобраться в том, как работают:

- сборка и запуск контейнеров
- сетевое взаимодействие между сервисами
- reverse proxy
- stateful и stateless workloads
- persistent storage
- healthchecks и probes
- troubleshooting в Docker и Kubernetes
- CI, доставка образов и ручной deploy flow

## Примечание

Проект учебный. Он используется как практический стенд для отработки навыков Go backend, контейнеризации, Kubernetes, CI/CD и troubleshooting.

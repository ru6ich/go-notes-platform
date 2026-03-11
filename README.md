# go-notes-platform

Учебный DevOps/SRE-проект вокруг простого приложения для заметок.

Проект начинался как контейнерный стенд на Docker Compose, а на текущем этапе уже перенесён в Kubernetes, получил CI в GitHub Actions, публикацию Docker-образов в GHCR и ручной deploy по SHA.

## Current status

На текущем этапе реализованы:

- Go API
- PostgreSQL
- nginx reverse proxy
- Python reporter
- Dockerfile для API и reporter
- запуск стека через Docker Compose
- перенос стека в Kubernetes
- blind troubleshooting-сценарии в Kubernetes
- GitHub Actions CI
- публикация образов в GHCR
- ручной deploy конкретного SHA в Kubernetes

## Architecture

### Docker Compose stage

```text
client -> localhost:8081 -> nginx:80 -> api:8080 -> postgres:5432
                               ^
                               |
                        reporter -> http://nginx/healthz
```

### Kubernetes stage

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

## Kubernetes resources

Текущая k8s-архитектура разложена так:

- `postgres` -> `StatefulSet + Service + PVC`
- `api` -> `Deployment + Service`
- `nginx` -> `Deployment + Service`
- `reporter` -> `Deployment + PVC`
- общие env-переменные -> `ConfigMap`
- пароль БД -> `Secret`

## Repository structure

```text
.
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
├── .github/
│   └── workflows/
│       └── ci.yml
├── nginx/
│   └── nginx.conf
├── reporter/
├── Dockerfile.api
├── Dockerfile.reporter
├── compose.yaml
└── README.md
```

## Run with Docker Compose

### Start

```bash
docker compose up --build
```

### Check

```bash
docker compose ps
docker compose logs -f
curl http://localhost:8081/healthz
curl http://localhost:8081/notes
```

### Stop

```bash
docker compose down
```

## Run with Kubernetes

Ниже пример локального запуска через Minikube.

### 1. Start Minikube

```bash
minikube start --driver=docker
kubectl config current-context
kubectl get nodes
```

### 2. Build local images inside Minikube

```bash
eval $(minikube -p minikube docker-env)

docker build -t go-notes-api:local -f Dockerfile.api .
docker build -t go-notes-reporter:local -f Dockerfile.reporter .
```

### 3. Apply manifests

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-config.yaml
kubectl apply -f k8s/02-postgres.yaml
kubectl apply -f k8s/03-api.yaml
kubectl apply -f k8s/04-nginx.yaml
kubectl apply -f k8s/05-reporter.yaml
```

### 4. Check cluster objects

```bash
kubectl -n go-notes-platform get all,pvc
```

### 5. Access application

```bash
kubectl -n go-notes-platform port-forward svc/nginx 8081:80
```

In another terminal:

```bash
curl http://localhost:8081/healthz
curl http://localhost:8081/notes
```

## CI/CD status

### CI

В репозитории настроен GitHub Actions workflow, который:

- запускается на `push`
- запускается на `pull_request`
- вручную запускается через `workflow_dispatch`

Он проверяет:

- Go API (`go test` и `go build`)
- Python reporter
- сборку Docker-образа API
- сборку Docker-образа reporter

### Image delivery

После успешного CI workflow публикует Docker-образы в GHCR.

Используются образы вида:

- `ghcr.io/ru6ich/go-notes-api:latest`
- `ghcr.io/ru6ich/go-notes-api:<commit-sha>`
- `ghcr.io/ru6ich/go-notes-reporter:latest`
- `ghcr.io/ru6ich/go-notes-reporter:<commit-sha>`

### Manual deploy by SHA

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

После проверки rollout SHA фиксируется в `k8s/03-api.yaml` и `k8s/05-reporter.yaml`, чтобы source of truth снова был в манифестах.

## Reporter outputs

Reporter stores generated reports in `/app/reports`.

Expected files:

- `summary.csv`
- `latency.png`
- `success_rate.png`
- `stats.json`

Check them in Kubernetes:

```bash
kubectl -n go-notes-platform exec deploy/reporter -- ls -la /app/reports
kubectl -n go-notes-platform exec deploy/reporter -- cat /app/reports/stats.json
```

## Useful Kubernetes commands

```bash
kubectl -n go-notes-platform get pods,svc,endpoints,pvc
kubectl -n go-notes-platform describe pod <pod-name>
kubectl -n go-notes-platform logs deploy/<deployment-name>
kubectl -n go-notes-platform exec -it <pod-name> -- sh
kubectl -n go-notes-platform port-forward svc/<service-name> 8081:80
```

## Progress by stages

Completed:

- Dockerfile for API and reporter
- nginx reverse proxy
- Docker Compose orchestration
- Compose troubleshooting
- Kubernetes namespace/config/secret
- PostgreSQL in Kubernetes
- API in Kubernetes
- nginx in Kubernetes
- reporter in Kubernetes
- first blind Kubernetes troubleshooting scenario
- GitHub Actions CI
- image publishing to GHCR
- manual SHA-based deployment flow

Next:

- more Kubernetes troubleshooting scenarios
- validation of Kubernetes manifests in CI
- linting and stronger checks
- possible future deploy automation

## Notes

This project is educational.

The main goal is not only to run the stack, but to understand:

- container build and runtime separation
- service-to-service networking
- reverse proxy behavior
- stateful vs stateless workloads
- persistent storage
- healthchecks and probes
- troubleshooting in Docker and Kubernetes
- CI, image delivery and manual deploy flow

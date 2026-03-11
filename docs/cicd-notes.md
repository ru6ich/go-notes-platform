# CI/CD notes

## Current CI/CD level

На текущем этапе в проекте реализована следующая схема:

```text
git push / pull request
        |
        v
GitHub Actions CI
  - Go API check
  - Reporter check
  - Docker image build check
        |
        v
GHCR image publish
  - go-notes-api:latest
  - go-notes-api:<sha>
  - go-notes-reporter:latest
  - go-notes-reporter:<sha>
        |
        v
Manual deploy by SHA
  - kubectl set image
  - kubectl rollout status
        |
        v
Kubernetes cluster
```

## What is already automated

### CI

Workflow in `.github/workflows/ci.yml` does:

- checkout repository
- setup Go
- `go mod download`
- `go test ./...`
- `go build ./cmd/api`
- setup Python
- install reporter dependencies
- syntax validation for reporter
- Docker build for API image
- Docker build for reporter image

### Image delivery

После успешных проверок workflow публикует образы в GHCR.

Используются:

- `latest`
- `<commit-sha>`

### Manual deployment

Автоматический deploy не настраивался намеренно.

Вместо этого используется ручной deploy по SHA:

```bash
kubectl -n go-notes-platform set image deployment/api \
  api=ghcr.io/ru6ich/go-notes-api:<SHA>

kubectl -n go-notes-platform set image deployment/reporter \
  reporter=ghcr.io/ru6ich/go-notes-reporter:<SHA>

kubectl -n go-notes-platform rollout status deployment/api
kubectl -n go-notes-platform rollout status deployment/reporter
```

## Why SHA-based deployment is useful

Deploy по SHA полезен потому что:

- образ жёстко привязан к конкретному коммиту
- проще понимать, что именно задеплоено
- проще откатываться
- это надёжнее, чем деплой по `latest`

## Why self-hosted runner was not added

Self-hosted runner не внедрялся в рамках текущего этапа.

Причины:

- проект публичный
- нужно сохранить безопасность основной машины
- для текущих учебных целей достаточно CI + image delivery + manual deploy

## What this stage teaches

Этот этап даёт практику по:

- базовому CI
- публикации Docker-образов
- работе с registry
- тегам образов
- связи commit SHA и image tag
- ручному rollout в Kubernetes
- диагностике rollout-проблем

## Current conclusion

Для текущего этапа лабораторной реализован хороший базовый CI/CD-процесс:

- код автоматически проверяется
- Docker-образы автоматически публикуются
- Kubernetes может получать эти образы из registry
- deploy выполняется вручную и контролируемо

Это уже достаточно хороший и реалистичный уровень для учебного проекта перед стажировкой.

## Possible future improvements

Позже можно усилить этап следующим:

- validation для k8s manifests в CI
- линтеры
- более строгие тесты
- release tags
- отдельный private deploy repo
- self-hosted runner в изолированной VM

# Kubernetes Cheatsheet

Короткая практическая шпаргалка для диагностики и повседневной работы.

---

## Базовая логика диагностики

Запомнить как цепочку:

**вижу → объясняю → читаю → захожу → проверяю**

- `get` — что вообще есть и в каком состоянии
- `describe` — почему объект в таком состоянии
- `logs` — что говорит само приложение
- `exec` — что происходит внутри контейнера
- `port-forward` — работает ли сервис снаружи

---

## Самые нужные команды

### Посмотреть общее состояние

```bash
kubectl -n go-notes-platform get pods
kubectl -n go-notes-platform get svc
kubectl -n go-notes-platform get endpoints
kubectl -n go-notes-platform get pvc
kubectl -n go-notes-platform get all,pvc
```

### Посмотреть подробности объекта

```bash
kubectl -n go-notes-platform describe pod <pod-name>
kubectl -n go-notes-platform describe svc <service-name>
kubectl -n go-notes-platform describe deployment <deployment-name>
kubectl -n go-notes-platform describe statefulset <statefulset-name>
```

### Посмотреть логи

```bash
kubectl -n go-notes-platform logs <pod-name>
kubectl -n go-notes-platform logs deploy/<deployment-name>
kubectl -n go-notes-platform logs deploy/<deployment-name> -f
kubectl -n go-notes-platform logs <pod-name> -c <container-name>
```

### Зайти внутрь контейнера

```bash
kubectl -n go-notes-platform exec -it <pod-name> -- sh
kubectl -n go-notes-platform exec deploy/<deployment-name> -- ls -la /app
kubectl -n go-notes-platform exec deploy/<deployment-name> -- env
```

### Проверить сервис снаружи

```bash
kubectl -n go-notes-platform port-forward svc/<service-name> 8081:80
curl http://localhost:8081/healthz
curl http://localhost:8081/notes
```

---

## Очень полезные дополнительные команды

### Посмотреть реальный YAML объекта из кластера

```bash
kubectl -n go-notes-platform get svc api -o yaml
kubectl -n go-notes-platform get pod <pod-name> -o yaml
```

### Посмотреть labels у Pod

```bash
kubectl -n go-notes-platform get pod --show-labels
```

### Смотреть изменения в реальном времени

```bash
kubectl -n go-notes-platform get pods -w
```

### Посмотреть endpoints конкретного сервиса

```bash
kubectl -n go-notes-platform get endpoints api
kubectl -n go-notes-platform get endpoints nginx -o yaml
```

### Посмотреть события

```bash
kubectl -n go-notes-platform get events --sort-by=.metadata.creationTimestamp
```

---

## Быстрые сценарии диагностики

### Если не отвечает nginx

```bash
kubectl -n go-notes-platform get pods,svc,endpoints
kubectl -n go-notes-platform describe pod -l app=nginx
kubectl -n go-notes-platform logs deploy/nginx --tail=50
```

### Если Service существует, но приложение не работает

```bash
kubectl -n go-notes-platform describe svc api
kubectl -n go-notes-platform get endpoints api
kubectl -n go-notes-platform get pod --show-labels
```

### Если база не стартует

```bash
kubectl -n go-notes-platform get pods,pvc
kubectl -n go-notes-platform describe pod postgres-0
kubectl -n go-notes-platform logs postgres-0
```

### Если Pod завис в `Init`

```bash
kubectl -n go-notes-platform describe pod <pod-name>
kubectl -n go-notes-platform logs <pod-name> -c <init-container-name>
```

### Если нужно посмотреть файлы внутри контейнера

```bash
kubectl -n go-notes-platform exec deploy/reporter -- ls -la /app/reports
kubectl -n go-notes-platform exec deploy/reporter -- cat /app/reports/stats.json
```

---

## Самое важное по сущностям

- `Pod` — где реально крутится контейнер
- `Deployment` — кто следит, чтобы stateless Pod был жив
- `StatefulSet` — контроллер для stateful-сервиса
- `Service` — стабильный адрес до Pod'ов
- `ConfigMap` — обычные настройки
- `Secret` — секретные настройки
- `PVC` — постоянный диск
- `initContainer` — подготовительный контейнер перед основным
- `readinessProbe` — можно ли уже слать трафик
- `livenessProbe` — не пора ли перезапустить контейнер

---

## Минимальный набор наизусть

```bash
kubectl get
kubectl describe
kubectl logs
kubectl exec
kubectl port-forward
```

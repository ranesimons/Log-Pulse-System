#!/usr/bin/env bash
set -euo pipefail

CLUSTER=logpulse

# ── Cluster ───────────────────────────────────────────────────────────────────
# Always recreate so extraPortMappings in kind-config.yaml are applied.
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER}$"; then
  echo "Deleting existing cluster..."
  kind delete cluster --name ${CLUSTER}
fi
echo "Creating kind cluster..."
kind create cluster --config k8s/kind-config.yaml

# ── Build images ──────────────────────────────────────────────────────────────
echo "Building images..."
docker build -t logpulse-backend:latest  ./backend
docker build -t logpulse-frontend:latest ./frontend

# ── Load images into kind ─────────────────────────────────────────────────────
echo "Loading images into kind..."
kind load docker-image logpulse-backend:latest  --name ${CLUSTER}
kind load docker-image logpulse-frontend:latest --name ${CLUSTER}

# ── Apply manifests ───────────────────────────────────────────────────────────
echo "Applying manifests..."
kubectl apply -f k8s/secret-local.yaml
kubectl apply -f k8s/nginx-configmap.yaml
kubectl apply -f k8s/postgres-configmap.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# ── Wait for readiness ────────────────────────────────────────────────────────
echo "Waiting for pods..."
kubectl rollout status deployment/postgres --timeout=90s
kubectl rollout status deployment/backend  --timeout=90s
kubectl rollout status deployment/frontend --timeout=90s

echo ""
echo "Log Pulse is running!"
echo "  Frontend : http://localhost:3000"
echo "  API docs : http://localhost:8000/docs"
echo ""
echo "To seed 100K rows:"
echo "  kubectl run seed --image=logpulse-backend:latest --image-pull-policy=IfNotPresent --restart=Never \\"
echo "    --overrides='{\"spec\":{\"hostNetwork\":true}}' \\"
echo "    --env=DATABASE_URL=postgresql://logpulse:logpulse@localhost:5432/logpulse \\"
echo "    -- python scripts/seed.py"
echo ""
echo "To tear down: kind delete cluster --name ${CLUSTER}"

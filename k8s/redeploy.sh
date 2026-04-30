#!/usr/bin/env bash
set -euo pipefail

CLUSTER=logpulse

docker build -t logpulse-backend:latest  ./backend
docker build -t logpulse-frontend:latest ./frontend

kind load docker-image logpulse-backend:latest  --name ${CLUSTER}
kind load docker-image logpulse-frontend:latest --name ${CLUSTER}

kubectl apply -f k8s/nginx-configmap.yaml
kubectl apply -f k8s/postgres-configmap.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

kubectl rollout restart deployment/backend
kubectl rollout restart deployment/frontend

kubectl rollout status deployment/backend
kubectl rollout status deployment/frontend

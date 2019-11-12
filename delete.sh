#!/bin/bash
set -e
kubectl delete replicaset -l app=jupyterhub
kubectl delete deployment -l app=jupyterhub
kubectl delete service -l app=jupyterhub
kubectl delete pod -l app=jupyterhub
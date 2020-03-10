#!/bin/bash
set -e
helm delete jhub
kubectl delete all -l app=jupyterhub

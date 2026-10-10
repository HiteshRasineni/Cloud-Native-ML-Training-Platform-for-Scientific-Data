#!/bin/bash
set -e
# Manual tool install when devcontainer features didn't provision (old Codespace)
echo "=== Alpine host detected: installing docker via apk ==="
if ! command -v docker >/dev/null 2>&1; then
  sudo apk add --no-cache docker docker-compose curl 2>/dev/null || apk add --no-cache docker docker-compose curl || sudo apk add --no-cache docker docker-cli-compose curl
  sudo service docker start 2>/dev/null || sudo dockerd > /tmp/dockerd.log 2>&1 &
  sleep 6
fi
docker --version 2>/dev/null || sudo docker --version || echo "docker daemon starting, check /tmp/dockerd.log"
echo "=== installing kubectl (static binary, no apt) ==="
if ! command -v kubectl >/dev/null 2>&1; then
  curl -sLO "https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl"
  chmod +x kubectl
  mkdir -p $HOME/.local/bin
  mv kubectl $HOME/.local/bin/kubectl
  export PATH=$HOME/.local/bin:$PATH
fi
$HOME/.local/bin/kubectl version --client 2>/dev/null || kubectl version --client
echo "=== installing kind ==="
if ! command -v kind >/dev/null 2>&1; then
  curl -sLo /tmp/kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64
  chmod +x /tmp/kind
  mkdir -p $HOME/.local/bin
  mv /tmp/kind $HOME/.local/bin/kind
  export PATH=$HOME/.local/bin:$PATH
fi
$HOME/.local/bin/kind version 2>/dev/null || kind version
echo "ALL TOOLS READY"

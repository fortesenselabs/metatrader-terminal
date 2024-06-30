#!/usr/bin/sh


# Tools:
# - [Minikube](https://minikube.sigs.k8s.io/docs/start/)
# - [Skaffold](https://skaffold.dev/docs/install/)
# - [Helm](https://helm.sh/docs/intro/install/)
# - [Tilt](https://docs.tilt.dev/install/)
# - [Go >= 1.18](https://go.dev/doc/install)
# - [Node >= 16.14](https://nodejs.org/en/download/)
# - [Python >= 3.10](https://www.python.org/downloads/)
# - [yq](https://github.com/mikefarah/yq)
# - [volta](https://volta.sh/)
# - [doctl](https://github.com/digitalocean/doctl)

# Skaffold
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/v2.11.1/skaffold-linux-amd64 && chmod +x skaffold && sudo mv skaffold /usr/local/bin

# yq
sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq &&\
    chmod +x /usr/bin/yq
# sudo chmod +x /usr/bin/yq

# volta
curl https://get.volta.sh | bash

# doctl
go install github.com/digitalocean/doctl/cmd/doctl@latest

# tilt
curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash


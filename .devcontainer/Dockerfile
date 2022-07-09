# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.241.1/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version (use -bullseye variants on local arm64/Apple Silicon): 3, 3.10, 3.9, 3.8, 3.7, 3.6, 3-bullseye, 3.10-bullseye, 3.9-bullseye, 3.8-bullseye, 3.7-bullseye, 3.6-bullseye, 3-buster, 3.10-buster, 3.9-buster, 3.8-buster, 3.7-buster, 3.6-buster
ARG VARIANT="3.10-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Choice] Node.js version: none, lts/*, 16, 14, 12, 10
ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

#--------
RUN curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null

RUN apt-get update && apt-get install -y \
    python3.10 \
    zip \
    jq \
    gpg \
    libssl-dev \
    libffi-dev \
    apt-transport-https \
    lsb-release \
    software-properties-common \
    wget \
    ca-certificates \
    gnupg \
    git \
    curl \
    python3-pip \
    nano \
    vim \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*


# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Terraform
RUN wget https://releases.hashicorp.com/terraform/1.1.7/terraform_1.1.7_linux_arm64.zip
RUN unzip terraform*.zip
RUN mv terraform /usr/local/bin

# Kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VER}/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin

# Kustomize
RUN curl -sL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VER}/kustomize_v${KUSTOMIZE_VER}_linux_amd64.tar.gz" | \
  tar -xz -C "/usr/bin" kustomize \
  && chmod +x /usr/bin/kustomize
## RUN curl -L https://github.com/kubernetes-sigs/kustomize/releases/download/v${KUSTOMIZE_VER}/kustomize_${KUSTOMIZE_VER}_linux_amd64  -o /usr/bin/kustomize \
#    && chmod +x /usr/bin/kustomize

# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb |  bash

# Flux
RUN curl -s https://fluxcd.io/install.sh | bash

# SOPS
ADD https://github.com/mozilla/sops/releases/download/v${SOPS_VER}/sops-v${SOPS_VER}.linux /usr/local/bin/sops
RUN chmod +x /usr/local/bin/sops

# AZCopy
RUN set -ex \
    && curl -L -o azcopy.tar.gz https://aka.ms/downloadazcopy-v10-linux \
    && tar -xf azcopy.tar.gz --strip-components=1 \
    && mv ./azcopy /usr/local/bin

# Fixing KeyVault bug in AZ CLI (issue/13507)
RUN pip3 uninstall azure-keyvault; \
    pip3 install azure-keyvault==1.1.0
#--------

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# [Optional] Uncomment this line to install global node packages.
# RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g <your-package-here>" 2>&1
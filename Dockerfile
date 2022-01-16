FROM ubuntu:latest
ENV TZ=America/New_York \
    DEBIAN_FRONTEND=noninteractive

LABEL "author"="Reuben Cleetus"
LABEL "version"="1.0"
LABEL "email"="reuben@cleet.us"
ENV SOPS_VER 3.7.1
ENV KUSTOMIZE_VER 2.0.0

#apt-get
RUN curl -sL https://packages.microsoft.com/keys/microsoft.asc gpg --dearmor | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null

RUN apt-get update && apt-get install -y \
    zip \
    jq \
    gpg \
    libssl-dev \
    libffi-dev \
    python-dev \
    apt-transport-https \
    lsb-release \
    software-properties-common \
    wget \
    ca-certificates \
    gnupg \
    git \
    azure-cli 

#Terraform
RUN wget https://releases.hashicorp.com/terraform/1.0.1/terraform_1.0.1_linux_amd64.zip
RUN unzip terraform*.zip
RUN mv terraform /usr/local/bin

#Kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin

#Kustomize
RUN curl -L https://github.com/kubernetes-sigs/kustomize/releases/download/v${KUSTOMIZE_VER}/kustomize_${KUSTOMIZE_VER}_linux_amd64  -o /usr/bin/kustomize \
    && chmod +x /usr/bin/kustomize

#SOPS
ADD https://github.com/mozilla/sops/releases/download/v${SOPS_VER}/sops-v${SOPS_VER}.linux /usr/local/bin/sops
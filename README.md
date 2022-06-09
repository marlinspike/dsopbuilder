[![Continuous Build, Test, Deploy](https://github.com/marlinspike/dsopbuilder/actions/workflows/docker-build.yml/badge.svg)](https://github.com/marlinspike/dsopbuilder/actions/workflows/docker-build.yml)

# DSOPBuilder and PyBuilder #

DevSecOps Builder (DSOPBuilder) is the complete toolset to create a Platform One Big Bang DevSecOps stack on Azure, running on Rancher RKE2 or Azure Kubernetes Service. The toolset consists of the following:

- DSOPBuilder Docker Image: The docker image contains all the required tools and the cloned Git Repos to deploy the Azure Infrastructure using Terraform.
- PyBuilder: The *PyBuilder* Python app provides an easy way to deploy the entire stack and automates many manual steps. PyBuilder allows you to configure the Terraform _tfvars_ file for both RKE2 and AKS via the config files provided.

The total deploy time is approximately *6-7 minutes*.

## Running DSOP Builder ##

The [DSOPBuilder Docker image](https://hub.docker.com/r/shuffereu/dsopbuilder) is automatically built and pushed to my DockerHub container repository. The DSOPBuilder image contains the PyBuilder app you'll use to deploy P1 DevSecOps to Azure.

### Pulling the image from DockerHub ##

First make sure you have [Docker Desktop](https://docs.docker.com/get-docker/) or [Rancher Desktop](https://rancherdesktop.io/) installed on your machine. To pull the image:

`docker pull shuffereu/dsopbuilder`

### Running the image ###

To run the image you pulled earlier:

`docker run -it shuffereu/dsopbuilder`

The `-it` parameter tells Docker that you want to shell into the running container.

## Configuring PyBuilder ##

PyBuilder uses 3 configuration files, found in `config/`.

### Configuring PyBuilder for Kubernetes deployments ###

The PyBuilder Kubernetes configuration files, found at *config/config-rke2.json* or *config/config-aks.json*, must be configured prior to deployment. Here is what the files looks like:

```json
{
    "general": {
        "cluster_name": "dsop_rke2",
        "cloud": "AzureUSGovernmentCloud",
        "location": "usgovvirginia"
    },
    "cluster-size": {
        "server_instance_count": 1,
        "agent_instance_count": 2,
        "vm_size": "Standard_D8_v3"
    },
    "connectivity": {
        "server_public_ip": "true",
        "server_open_ssh_public": "true"
    },
    "custom_vnet_settings" : {
        "vnet_customize": 0,
        "use_external_vnet": 0,
        "external_vnet_resource_group" : "rke2_rg",
        "external_vnet_name" : "rke2-vnet",
        "external_vnet_subnet_name" : "rke2-subnet"
    },
    "custom_aad_settings_for_aks" : {
        "aad_group_ids" : ["00000000-0000-0000-0000-000000000000"]
    },
    "clone_dsop_repo_name": "dsop_rke2"
  } 
```

Here's what the parameters mean:

**General**

- cluster_name: The name of the RKE2 Kubernetes Cluster
- cloud: "AzureUSGovernmentCloud" here means Azure Government
- location: The Azure Region to deploy in

**Cluster-Size**

- server_instance_count: Number of masters
- agent_instance_count: Number of nodes required
- vm_size: Azure VM SKU. Make sure this SKU exists in the Cloud and Region configured

**Connectivity**

- server_public_ip: True if you need a Public IP for your cluster; False otherwise

**RBAC**

- aad_group_ids: *(AKS Only)* A list of Azure Active Directory Group IDs that will be granted privileges to the AKS cluster that is deployed.

### Configuring PyBuilder for Big Bang Deployment ###

The PyBuilder Big Bang configuration file, found at *config/config-bigbang.json*, must be configured prior to deployment. Here is what the files looks like:

```json
{
  "credentials": {
      "github_user" : "__GH_USER__",
      "github_pat" : "__GH_PAT__",
      "ironbank_user" : "__IB_USER__",
      "ironbank_pat" : "__IB_PAT__"
  },
  "bigbang" : {
      "hostname" : "bigbang.dev",
      "azure_deploy_name": "bigbang",
      "namespace": "bigbang",
      "repository" : {
          "url" : "__GH_REPO__",
          "branch": "__GH_BRANCH__"
      },
      "keys": {
          "gpg_key_name" : "bigbang-sops",
          "create_keys" : 1,
          "upload_keys" : 0,
          "istio-gw-crt": "<akv-secret-id?>",
          "istio-gw-key": "<akv-secret-id?>"
      },
      "flux": {
          "deploy_flux" : 1            
      }
  }
}
```

Here's what the parameters mean:

**Credentials**

- github_user - Your GitHub username
- github_pat - A GitHub Personal Access Token, used to commit Big Bang configurations to GitHub.
- ironbank_user - Your IronBank username
- ironbank_pat  - Your IronBank Personal Access Token, used by Flux to pull images from IronBank.

**Big Bang**

- hostname - hostname prefix for the Big Bang components in your cluster. We recommend `bigbang.dev`
- azure_deploy_name
- namespace - k8s namespace that bigbang will be deployed into
- repository.url - repository url where you will store your Big Bang deployment configurations (for Flux). *e.g.* `https://www.github.com/<org | username>/<repository>`
- repository.branch - a branch under that repository where the configuration will be stored. Usually we recommend using the pattern `env/<env-name>`
- keys.gpg_key_name -
- keys.create_keys - 1 or 0. If 1, gpg keys and self-signed certs will be generated. Only 1 has been tested thus far.
- keys.upload_keys - 1 or 0. Future functionality; keep set to 0.
- keys.istio-gw-crt - Future functionality; do not change
- keys.istio-gw-key - Future functionality; do not change
- flux.deploy_flux - 1 or 0. If 1, flux will be installed on the cluster prior to deploying Big Bang. Only 1 has been tested thus far.

## Running PyBuilder ##

PyBuilder is a Python3 app. Everything else needed by PyBuilder is already installed in the Docker iamge). Basic usage of PyBuilder:

Jump to **[Deploying RKE2](#the-rke2-command-creating-an-rke2-cluster-in-azure)** - **[Deploying AKS](#the-aks-command-creating-an-azure-kubernetes-service-aks-cluster-in-azure)** - **[Deploying Big Bang](#the-bb-command-deploying-bigbang-on-a-kubernetes-cluster-in-azure)** - **[Settings](#the-settings-command-configuring-pybuilder-and-logging-into-azure)**

PyBuilder's command interface is easy to use, and help is built in.

*Command*: `python3 main.py --help`

This prints out the following information:

```text
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  aks       Apply settings and build an AKS Cluster in Azure
  bb        Apply settings and deploy Big Bang to a K8S Cluster in Azure
  main      Deprecated.
  rke2      Apply settings and build a Rancher RKE2 Cluster in Azure
  settings  Show and configure Settings information
```

### The settings command: Configuring PyBuilder and Logging into Azure ###

PyBuilder requires you to be logged in to Azure so that you can apply the Terraform needed and interact with Azure resources. It is easy to do that through the settings command.

*Command*: `python3 main.py settings --help`

This prints out the following information:
```
Usage: main.py settings [OPTIONS] COMMAND [ARGS]...

  Show and configure Settings information

Options:
  --help  Show this message and exit.

Commands:
  azaccount   List the currently logged in account
  azlist      Lists all registered Clouds, Prints Cloud status
  azlogingov  Switches to AzureUSGovernment cloud and executes an az login 
  list        Lists the current configuration settings (config.json)
  validate    Validates the settings in the config.json file
```

- Use the *azaccount* subcommand to show the currently logged in Azure Account

```text
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Cloud Name        ┃ Is Default ┃ Tenant ID                            ┃ User                                         ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ AzureUSGovernment │ True       │ 4*******-b***-4***-a***-0*********** │ ******@**********************onmicrosoft.com │
└───────────────────┴────────────┴──────────────────────────────────────┴──────────────────────────────────────────────┘
```

- Use the *azlist* subcommand to show the currently Active Azure Cloud

```text
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Cloud Name        ┃ Is Active ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ AzureCloud        │ False     │
│ AzureChinaCloud   │ False     │
│ AzureUSGovernment │ True      │
│ AzureGermanCloud  │ False     │
└───────────────────┴───────────┘
```

- Use the *azlogingov* subcommand to Switch to and Login to Azure US Government
- Use the *list* subcommand to print the current config.json file
- Use the *validate* subcommand to validate the config.json file

### The `rke2` command: Creating an rke2 Cluster in Azure

`python3 main.py rke2 apply`

Depends on [configuration](#configuring-pybuilder-for-kubernetes-deployments) in `config/config-rke2.json`.

This command applies the Terraform to build out the Rancher RKE2 cluster in Azure. PyBuilder prompts you for a **Project Name**, which is a folder that it creates and initializes with the Terraform scripts needed.

**Important:** The final step to being able to use *kubectl* to control your cluster requires you to execute the script file indicated after you've run *rke2 apply*.

```bash
Deployment Completed!
Your deployment folder is: /PyBuilder/working/dsop_rke2/foo
Next Steps:
1. Change to the deployment folder:  cd working/dsop_rke2/foo
2. Export the KubeConfig:  source ../scripts/fetch-kubeconfig.sh
```

### The `aks` command: Creating an Azure Kubernetes Service (AKS) cluster in Azure

Depends on [configuration](#configuring-pybuilder-for-kubernetes-deployments) in `config/config-aks.json`.

`python3 main.py aks apply`

This command applies the Terraform to build out an Azure Kubernetes Service (AKS) cluster in Azure. PyBuilder prompts you for a **Project Name**, which is a folder that it creates and initializes with the Terraform scripts needed.

**Important 1:** This deploys AKS with limited RBAC permissions. You must supply an Azure Active Directory (AAD) Group ID that will maintain access rights to the cluster. All users who wish to access the cluster must be part of this AAD Group. This is set in config.json as `aad_group_ids` setting - it is a list of Group IDs.

**Important 2:** The final step to being able to use *kubectl* to control your cluster requires you to use `az aks get-credentials` to obtain cluster configuration.

```bash
Deployment Completed!
Your deployment folder is: /PyBuilder/working/dsop_aks/foo
Next Steps:
1. Change to the deployment folder:  cd working/dsop_aks/foo
2. Set KubeConfig:  az aks get-credentials -g $(terraform output -raw rg_name) -n $(terraform output -raw aks_cluster_name)
```

### The `bb` command: Deploying BigBang on a Kubernetes cluster in Azure ###

Depends on [configuration](#configuring-pybuilder-for-big-bang-deployment) in `config/config-bigbang.json`.

`python3 main.py bb deploy`

This command automates the deployment of BigBang, as documented in [Repo1](a) to a Kubernetes cluster running in Azure.

#### Pre-requisites ####

- Must be logged in to Azure via the [Azure CLI](#the-settings-command-configuring-pybuilder-and-logging-into-azure).
- Must have a Kubernetes cluster (RKE2 or AKS) running in Azure, with `kubectl`'s conf set (*i.e.,* You should be able to run `kubectl version` and have it complete successfully).

#### General steps executed by PyBuilder ####

1. **Validates that the settings** in `config-bigbang.json` have been updated.
1. **Verifies that you have an active K8s cluster** in your running environment by executing `kubectl version`.
1. **Configures Git Global User** for pushes to the repository and branchin your config file.
1. **Creates GPG Certificates and Keys** for use by Istio, if configured to do so, and adds them to `secrets.yaml`
1. **Updates `bigbang.yaml` configuration** and pushes to your Git repository.
1. **Prepares the Kubernetes Cluster** with the required secrets, credentials, and namespaces.
1. **Deploys Flux to the Kubernetes Cluster**, if configured to do so.
1. **Deploys BigBang to the Kubernetes Cluster**.

This process usually completes in less than *2 minutes*.

#### Verifying the installation ####

After this completes, you can run the following command to watch Flux deploy BigBang to your cluster.

`python3 main.py bb verify`

It will print out a screen similar to the following

```text
NAMESPACE   NAME                                                          URL                                                                              READY     STATUS           
AGE
bigbang     gitrepository.source.toolkit.fluxcd.io/bigbang                https://repo1.dso.mil/platform-one/big-bang/bigbang.git                          True      Fetched revision:
1.29.0/9da211a129a13617cbd0f3b710d85333488f6561               31s
bigbang     gitrepository.source.toolkit.fluxcd.io/cluster-auditor        https://repo1.dso.mil/platform-one/big-bang/apps/core/cluster-auditor.git        True      Fetched revision:
1.4.0-bb.0/a3c9fc97f6b25b02e4e7f32d5508469a1c0c0b92           14s

....

NAMESPACE   NAME                                                 READY     STATUS                                                  AGE
bigbang     helmrelease.helm.toolkit.fluxcd.io/bigbang           True      Release reconciliation succeeded                        31s
bigbang     helmrelease.helm.toolkit.fluxcd.io/cluster-auditor   False     dependency 'bigbang/gatekeeper' is not ready            14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/eck-operator      False     HelmChart 'bigbang/bigbang-eck-operator' is not ready   14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/ek                False     dependency 'bigbang/eck-operator' is not ready          14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/fluent-bit        False     dependency 'bigbang/ek' is not ready                    14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/gatekeeper        Unknown   Reconciliation in progress                              14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/istio             False     dependency 'bigbang/istio-operator' is not ready        14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/istio-operator    False     dependency 'bigbang/gatekeeper' is not ready            14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/jaeger            False     dependency 'bigbang/istio' is not ready                 14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/kiali             False     dependency 'bigbang/istio' is not ready                 14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/monitoring        False     HelmChart 'bigbang/bigbang-monitoring' is not ready     14s
bigbang     helmrelease.helm.toolkit.fluxcd.io/twistlock         False     dependency 'bigbang/gatekeeper' is not ready            14s

```

Flux refers to this as *reconciliation* because it is watching your Git repository for configuration changes, and the reconciles any changes into your cluster.

Once all of the statuses in the READY column turn to TRUE, Big Bang is ready to start being used.
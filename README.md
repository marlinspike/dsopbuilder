[![Continuous Build, Test, Deploy](https://github.com/marlinspike/dsopbuilder/actions/workflows/docker-build.yml/badge.svg)](https://github.com/marlinspike/dsopbuilder/actions/workflows/docker-build.yml)

# DSOPBuilder and PyBuilder #
DevSecOps Builder (DSOPBuilder) is the complete toolset to create a Platform One Big Bang DevSecOps stack on Azure, running on Rancher RKE2. The toolset consists of the following:
- DSOPBuilder Docker Image: The docker image contains all the required tools and the cloned Git Repos to deploy the Azure Infrastructure using Terraform.
- PyBuilder: The *PyBuilder* Python app provides an easy way to deploy the entire stack and automates many manual steps. PyBuilder allows you to configure the Terraform _tfvars_ file via the config file provided.

The total deploy time is approximately *6-7 minutes*.

### Running DSOP Builder ###
The [DSOPBuilder Docker image](https://hub.docker.com/r/shuffereu/dsopbuilder) is automatically built and pushed to my DockerHub container repository. The DSOPBuilder image contains the PyBuilder app you'll use to deploy P1 DevSecOps to Azure.

## Pulling and Running the Image from DockerHub ##
First make sure you have [Docker Desktop](https://docs.docker.com/get-docker/) installed on your machine. To pull the image:
`docker pull shuffereu/dsopbuilder`

### Running the image ###
To run the image you pulled earlier:
`docker run -it shuffereu/dsopbuilder`
The _-it_ parameter tells Docker that you want to shell into the running container.

## Configuring PyBuilder
The PyBuilder configuration file, found at *config/config.json* must be configured. Here's what that file looks like:
```
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


## Running PyBuilder ##
PyBuilder is a Python3 app (Python3 and everything else you'll need is already installed in the Docker iamge). Basic usage of PyBuilder:

PyBuilder's command interface is easy to use, and help is built in.

*Command*: `python3 main.py --help`

This prints out the following information:
```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  main      Deprecated.
  rke2      Apply settings and build a Rancher RKE2 Cluster in Azure
  settings  Show and configure Settings information
```

### The settings command: Configuring PyBuilder and Logging into Azure

PyBuilder requires you to be logged in to Azure so that you can apply the Terraform needed, and makes it easy to do that through the settings command. 

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
  azlogingov  Switches to USGovCloud
  list        Lists the current configuration settings (config.json)
  validate    Validates the settings in the config.json file
```

- Use the *azaccount* subcommand to show the currently logged in Azure Account
```
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Cloud Name        ┃ Is Default ┃ Tenant ID                            ┃ User                                         ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ AzureUSGovernment │ True       │ 4*******-b***-4***-a***-0*********** │ ******@**********************onmicrosoft.com │
└───────────────────┴────────────┴──────────────────────────────────────┴──────────────────────────────────────────────┘
```

- Use the *azlist* subcommand to show the currently Active Azure Cloud
```
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


### The rke2 command: Creating an rke2 Cluster in Azure
`python3 main.py rke2 apply`

This command applies the Terraform to build out the Rancher RKE2 cluster in Azure. PyBuilder prompts you for a **Project Name**, which is a folder that it creates and initializes with the Terraform scripts needed.

**Important:** The final step to being able to use *kubectl* to control your cluster requires you to execute the script file indicated after you've run *rke2 apply*.

```
Deployment Completed!
Your deployment folder is: /PyBuilder/working/dsop_rke2/foo
Next Steps:
1. Change to the deployment folder:  cd working/dsop_rke2/foo
2. Export the KubeConfig:  source ../scripts/fetch-kubeconfig.sh
```

# DSOPBuilder and PyBuilder #
DevSecOps Builder (DSOPBuilder) is the complete toolset to create a Platform One Big Bang DevSecOps stack on Azure, running on Rancher RKE2. The toolset consists of the following:
- DSOPBuilder Docker Image: The docker image contains all the required tools and the cloned Git Repos to deploy the Azure Infrastructure using Terraform.
- PyBuilder: The *PyBuilder* Python app provides an easy way to deploy the entire stack and automates many manual steps. PyBuilder allows you to configure the Terraform _tfvars_ file via the config file provided.

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

- Run Post Installer: 
``` 
    cd working/dsop_rke2/example
    source run_after_deploy.sh 
```
- Executing the app: `python3 main.app --help`
- Displaying the variables you can configure: `python3 main.py --settings=y`
- Editing the values you need to modify for Terraform: Update the _config.json_ file in the _config_ folder with the values you'd like Terraform to use to deploy the solution. See the Section below that discusses each variable.
- Deploying the RKE2 Big Bang on Azure platform: `python3 main.app --deploy=y`
- Tearing down the cluster after you've created it: `python3 main.py --destroy=y`

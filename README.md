**DSOPBuilder and PyBuilder**
DevSecOps Builder (DSOPBuilder) is the complete toolset to create a Platform One Big Bang DevSecOps stack on Azure, running on Rancher RKE2. The toolset consists of the following:
- DSOPBuilder Docker Image: The docker image contains all the required tools and the cloned Git Repos to deploy the Azure Infrastructure using Terraform.
- PyBuilder: The *PyBuilder* Python app provides an easy way to deploy the entire stack and automates many manual steps. PyBuilder allows you to configure the Terraform _tfvars_ file via the config file provided.

*** Running DSOP Builder ***
The [DSOPBuilder Docker image](https://hub.docker.com/r/shuffereu/dsopbuilder) is automatically built and pushed to my DockerHub container repository. The DSOPBuilder image contains the PyBuilder app you'll use to deploy P1 DevSecOps to Azure.

*Pulling the Image from DockerHub*
First make sure you have [Docker Desktop](https://docs.docker.com/get-docker/) installed on your machine. To pull the image:
`docker pull shuffereu/dsopbuilder`

*Running the image*
To run the image you pulled earlier:
`docker run -it shuffereu/dsopbuilder`

*Running PyBuilder*
PyBuilder is a Python3 app (Python3 and everything else you'll need is already installed in the Docker iamge). Basic usage of PyBuilder:

- Executing the app: `python3 main.app --help`
- Displaying the variables you can configure: `python3 main.app --settings=y`
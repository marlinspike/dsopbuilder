from sqlite3 import Time
from util.streams import Stream
from util.k8s_streams import K8S_Stream
from appsettings import AppSettings
import pathlib
import util
from util.io import *
import os
from rich.console import Console
import time
import sys
import logging
from rich import print
from rich.panel import Panel
import typer
import command.settings as settings
import command.dsop_aks as dsop_aks

stream = Stream()
console = Console()
app = typer.Typer()

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
console = Console()

_app_settings = None
_working_dir = "working"
_clone_dsop_aks_dir = "dsop_aks"
_stream = None

@app.command()
def apply(
    project:str = typer.Option("foo", help="Project name for which to initialize Terraform and Scripts. Can be added to a git repo.",prompt="Project Name", confirmation_prompt=True),
    config:str = typer.Option("n", help="Print app config settings (these configure Azure Cloud Login and Terraform)"),
    destroy:str = typer.Option("n", help="Destroy the resources created by Terraform. If 'y', Destroy. USE WITH CARE!")):
    """
        Applies the AKS Terraform and builds the AKS Cluster in Azure.
    """
    Timed()
    _app_settings = AppSettings('./config/config-aks.json')
    #Ensure that app-settings are valid
    if(_app_settings.validate() == False):
        exit(1)
    
    _terraform_file = f"{str(pathlib.Path().resolve())}/{_working_dir}/{_clone_dsop_aks_dir}/{project}/terraform.tfvars"
    _stream = K8S_Stream(_clone_dsop_aks_dir, _working_dir, pathlib.Path().resolve(), project_dir=project)
    print(Panel.fit("PyBuilder - The Pythonic Azure Big Bang Deployment Tool"))


    if bool(_app_settings.settings["custom_vnet_settings"]["vnet_customize"]) == False:
        if os.path.isdir(f"{str(pathlib.Path().resolve())}/{_working_dir}") == False: _stream.Do_No_VNet_Customization()#No VNet Customization
        _stream.do_rename_terraform_file()
        _stream.create_project_dir()
        with console.status("Applying Config settings...", spinner="earth"):
            logger.debug("Applying config settings")
            splice_file_token(_terraform_file,"resource_group_name", f"{_app_settings.settings['general']['cluster_name']}-rg")
            splice_file_token(_terraform_file,"cluster_name", _app_settings.settings["general"]["cluster_name"])
            splice_file_token(_terraform_file, "cloud", _app_settings.settings["general"]["cloud"])
            splice_file_token(_terraform_file, "location", _app_settings.settings["general"]["location"])
            splice_file_token(_terraform_file, "server_public_ip", _app_settings.settings["connectivity"]["server_public_ip"])
            splice_file_token(_terraform_file, "server_open_ssh_public", _app_settings.settings["connectivity"]["server_open_ssh_public"])
            splice_file_list(_terraform_file, "aad_group_ids", _app_settings.settings["custom_aad_settings_for_aks"]["aad_group_ids"])
            splice_file_list(_terraform_file, "kubernetes_version", f"\"{_app_settings.settings['general']['kubernetes_version']}\"")
            cout_success("Completed Terraform Token splicing!")
        with console.status("Initializing Azure-CLI login...", spinner="earth"):
            logger.debug("Initializing Azure Cloud")
            if (settings.is_logged_in() == False):
                cout_error("You're not logged in to Azure. Please log in to Azure to continue.")
                cout_success("You can use the command: 'main.py settings azlogingov' to log in to Azure Government")
                exit(1)
        do_apply = typer.confirm("Continue with Terraform deploy?", abort=True)
        with console.status("Initializing Terraform...", spinner="earth"):
            logger.debug("Initializing Terraform")
            _stream._run_terraform_init()
            cout_success("Terraform Init Completed!")
        with console.status("Running Terraform... This may take a while: ", spinner="earth"):
            logger.debug("Running Terraform")
            _stream._run_terraform()
            cout_success("Deployment Completed!")
            cout_success(f"Your deployment folder is: {str(pathlib.Path().resolve())}/{_working_dir}/{_clone_dsop_aks_dir}/{project}")
            cout_success("Next Steps: ")
            cout_success(f"1. Change to the deployment folder:  cd {_working_dir}/{_clone_dsop_aks_dir}/{project}")
            cout_success(f"2. Set KubeConfig: az aks get-credentials -g $(terraform output -raw rg_name) -n $(terraform output -raw aks_cluster_name)")
            cout_success(f"3. After merging kubeconfig, run kubectl version to force AKS AAD device login.")
    else:
        #VNet Customization
        ...
    Timed()
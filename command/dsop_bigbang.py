from sqlite3 import Time
from util.streams import Stream
from appsettings import AppSettings
import pathlib
import util
from util.io import *
import os
#from rich.console import Console
import time
import sys
import logging
#from rich import print
#from rich.panel import Panel
import typer
import command.settings as settings
import command.dsop_rke2 as dsop_rke2

stream = Stream()
console = Console()
app = typer.Typer()



log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
console = Console()



_app_settings = None
_working_dir = "working"
_clone_dsop_rke2_dir = "dsop_rke2"
_clone_bigbang_dir = "bigbang"
_stream = None

@app.command()
def deploy_to_rke2(
    project:str = typer.Option("foo", help="Project name that you gave to your RKE2 deployment"),
    config:str  = typer.Option("n", help="Print app config settings (these configure Azure Cloud Login and Big Bang)"),
    akv:str     = typer.Option("", help="Name of an Azure Key Vault where KUBECONFIG can be retrived from and certs can be stored.")
    #destroy:str = typer.Option("n", help="Destroy the resources created by Terraform. If 'y', Destroy. USE WITH CARE!")
      ):
    """
        Deploys BigBang to a Rancher RKE2 Cluster in Azure, previously deployed via this tool.
    """
    Timed()
    _app_settings = AppSettings('./config/bigbang-config.json')
    
    #Ensure that app-settings are valid
    if(_app_settings.validate_bigbang() == False):
        exit(1)

    _rke2_stream = Stream(_clone_dsop_rke2_dir, _working_dir, pathlib.Path().resolve(), project_dir=project)
    _bb_stream   = Stream(_clone_bigbang_dir, _working_dir, pathlib.Path().resolve(), project_dir='dev')


    '''
    # Make sure you're logged into Azure
    with console.status("Initializing Azure-CLI login...", spinner="earth"):
        logger.debug("Initializing Azure Cloud")
        if (settings.is_logged_in() == False):
            cout_error("You're not logged in to Azure. Please log in to Azure to continue.")
            cout_success("You can use the command: main.py settings azloginusgov to log in to Azure Government")
            exit(1)
    '''

    # Create ISTIO certs

    if bool(_app_settings.settings["bigbang"]["keys"]["create_keys"]) == True:
        with console.status("Creating ISTIO Certs...", spinner="earth"):
            logger.debug("Creating ISTIO Certs...")

            _bb_stream.do_create_root_certs()
            _bb_stream.do_create_domain_certs(_app_settings.settings["bigbang"]["hostname"])

            # Upload certs if necessary
            if bool(_app_settings.settings["bigbang"]["keys"]["upload_keys"]) == True:
                logger.debug("Uploading ISTIO Certs...")
                _bb_stream.do_upload_domain_certs(_app_settings.settings["bigbang"]["hostname"], akv)

    # Update bigbang.yaml
    with console.status("Updating and pushing bigbang.yaml ...", spinner="earth"):
        logger.debug("Updating and pushing bigbang.yaml...")

        _bb_stream.do_reset_bigbang_yaml()

        _bb_stream.do_update_bigbang_yaml(
            _app_settings.settings["bigbang"]["repository"]["url"],
            _app_settings.settings["bigbang"]["repository"]["branch"]
        )

        _bb_stream.store_git_credentials(
            _app_settings.settings["credentials"]["github_user"], 
            _app_settings.settings["credentials"]["github_pat"]
        )

        _bb_stream.do_push_bigbang_yaml(
            _app_settings.settings["bigbang"]["repository"]["url"],
            _app_settings.settings["bigbang"]["repository"]["branch"]
        )

    # Update secrets.sh
    with console.status("Creating secrets.sh ...", spinner="earth"):
        logger.debug ("Creating secrets.sh...")

        _bb_stream.do_create_secrets_sh (
            _app_settings.settings["credentials"]["github_user"],
            _app_settings.settings["credentials"]["github_pat"],
            _app_settings.settings["credentials"]["ironbank_user"],
            _app_settings.settings["credentials"]["ironbank_pat"],
            _app_settings.settings["bigbang"]["hostname"]
        )

    # set kubeconfig

    with console.status ("Setting Kubeconfig...", spinner="earth"):
        logger.debug ("Setting Kubeconfig")

        _rke2_stream.fetch_kubeconfig()


    # Set deploy-vars.sh
    with console.status ("Setting deploy-vars.sh ...", spinner="earth"):
        logger.debug ("Setting deploy-vars.sh")

        _bb_stream.do_set_deploy_vars(kubeconfig_file=f"{_rke2_stream.get_project_dir()}/rke2.kubeconfig")
    


    # deploy

    with console.status ("Deploying Big Bang! This may take a while ...", spinner="earth"):
        _bb_stream.do_bigbang_deploy()



    '''
    _terraform_file = f"{str(pathlib.Path().resolve())}/{_working_dir}/{_clone_dsop_rke2_dir}/{project}/terraform.tfvars"
    _stream = Stream(_clone_dsop_rke2_dir, _working_dir, pathlib.Path().resolve(), project_dir=project)

    print(Panel.fit("PyBuilder - The Pythonic Azure Big Bang Deployment Tool\nReuben Cleetus - reuben@cleet.us\nwith Tim Meyers (BB Deployment)"))


    if bool(_app_settings.settings["custom_vnet_settings"]["vnet_customize"]) == False:
        if os.path.isdir(f"{str(pathlib.Path().resolve())}/{_working_dir}") == False: _stream.Do_No_VNet_Customization()#No VNet Customization
        _stream.do_rename_terraform_file()
        _stream.create_proejct_dir()
        with console.status("Applying Config settings...", spinner="earth"):
            logger.debug("Applying config settings")
            splice_file_token(_terraform_file,"cluster_name", _app_settings.settings["general"]["cluster_name"])
            splice_file_token(_terraform_file, "cloud", _app_settings.settings["general"]["cloud"])
            splice_file_token(_terraform_file, "location", _app_settings.settings["general"]["location"])
            splice_file_token(_terraform_file, "server_public_ip", _app_settings.settings["connectivity"]["server_public_ip"])
            splice_file_token(_terraform_file, "server_open_ssh_public", _app_settings.settings["connectivity"]["server_open_ssh_public"])
            cout_success("Completed Terraform Token splicing!")
        with console.status("Initializing Azure-CLI login...", spinner="earth"):
            logger.debug("Initializing Azure Cloud")
            if (settings.is_logged_in() == False):
                cout_error("You're not logged in to Azure. Please log in to Azure to continue.")
                cout_success("You can use the command: main.py settings azloginusgov to log in to Azure Government")
                exit(1)
                #_stream.do_cloud_login()
                #cout_success("Azure Login Completed.")
        do_apply = typer.confirm("Continue with Terraform deploy?", abort=True)
        with console.status("Initializing Terraform...", spinner="earth"):
            logger.debug("Initializing Terraform")
            _stream._run_terraform_init()
            cout_success("Terraform Init Completed!")
        with console.status("Running Terraform... This may take a while: ", spinner="earth"):
            logger.debug("Running Terraform")
            _stream._run_terraform()
            cout_success("Deployment Completed!")
            cout_success(f"Your deployment folder is: {str(pathlib.Path().resolve())}/{_working_dir}/{_clone_dsop_rke2_dir}/{project}")
            cout_success("Next Steps: ")
            cout_success(f"1. Change to the deployment folder:  cd {_working_dir}/{_clone_dsop_rke2_dir}/{project}")
            cout_success(f"2. Export the KubeConfig:  source ../scripts/fetch-kubeconfig.sh")

    else:
        #VNet Customization
        ...
    '''

    Timed()
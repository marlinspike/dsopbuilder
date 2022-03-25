from re import template
from sqlite3 import Time
from util.streams import *
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
#import command.dsop_rke2 as dsop_rke2

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

    _rke2_stream = RKE2_Stream(_clone_dsop_rke2_dir, _working_dir, pathlib.Path().resolve(), project_dir=project)
    _bb_stream   = BigBang_Stream(_clone_bigbang_dir, _working_dir, pathlib.Path().resolve(), project_dir='dev')

    '''
    # Make sure you're logged into Azure
    with console.status("Initializing Azure-CLI login...", spinner="earth"):
        logger.debug("Initializing Azure Cloud")
        if (settings.is_logged_in() == False):
            cout_error("You're not logged in to Azure. Please log in to Azure to continue.")
            cout_success("You can use the command: main.py settings azloginusgov to log in to Azure Government")
            exit(1)
    '''

    with console.status ("Verifying Kubernetes Cluster", spinner="earth"):
        logger.debug("Verifying Kubernetes Cluster")
        settings.kubeversion()


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

        _bb_stream.git_store_credentials(
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
        _stream.create_project_dir()
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

@app.command()
def rke2 (
    project:str = typer.Option("foo", help="Project name that you gave to your RKE2 deployment")
    ):
    """
        Take2: Deploys BigBang to a Rancher RKE2 Cluster in Azure, previously deployed via this tool.
    """

    Timed()

    _app_settings = AppSettings('./config/bigbang-config.json')
    _rke2_stream = RKE2_Stream(_clone_dsop_rke2_dir, _working_dir, pathlib.Path().resolve(), project_dir=project)
    _bb_stream   = BigBang_Stream(_clone_bigbang_dir, _working_dir, pathlib.Path().resolve(), project_dir='dev')


    #------- Validate settings; check Kubernetes ---------------

    validate_settings_and_environment(_app_settings, _bb_stream)

    #------- Create ISTIO certs and keys -------

    if bool(_app_settings.settings["bigbang"]["keys"]["create_keys"]) == True:
        create_istio_certs_and_keys(_app_settings, _bb_stream)

    # ------- Configure git -----------------------

    configure_git(_app_settings, _bb_stream)   

    # ------- Update bigbang.yaml -----------------------

    update_bigbang_yaml(_app_settings, _bb_stream)      

    # ------- Create GPG keys and get fingerprint ----------------------- 
    create_gpg_keys_and_update_sops_yaml(_app_settings, _bb_stream)

    # ------- Update and encrypt yaml secrets -----------------------
    update_secrets_yaml(_app_settings, _bb_stream)
    update_istio_yaml(_app_settings, _bb_stream)

    # ------- Configure kubernetes cluster - namespaces, secrets

    prepare_kubernetes (_app_settings, _bb_stream)
    
    if bool(_app_settings.settings["bigbang"]["flux"]["deploy_flux"]) == True:
        install_flux (_app_settings, _bb_stream)

    install_bigbang(_bb_stream)

    Timed()

@app.command()
def verify():
    _bb_stream   = BigBang_Stream(_clone_bigbang_dir, _working_dir, pathlib.Path().resolve(), project_dir='dev')
    command = f"get gitrepositories,ks,hr -A"
    
    _bb_stream.exec_kubectl_cmd(command)

def create_gpg_keys_and_update_sops_yaml(_app_settings, _bb_stream):
    fingerprint = None
    
    log_line = "Get GPG key fingerprint"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        gpg_key_name =  _app_settings.settings["bigbang"]["keys"]["gpg_key_name"]

        #_bb_stream.generate_gpg_keys(gpg_key_name)
        
        fingerprint = _bb_stream.get_gpg_fingerprint (gpg_key_name, create_if_needed=True)
        _bb_stream.generate_gpg_secret_file(fingerprint)

        cout_success ("Success - Obtained gpg fingerprint")    

    log_line = "Updating .sops.yaml"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        tokens = {"FALSE_KEY_HERE": fingerprint}

        template_file = f"{_bb_stream.get_work_dir()}/.sops.yaml.save"
        out_file = f"{_bb_stream.get_work_dir()}/.sops.yaml"
        create_file_from_template (template_file, out_file, tokens) 

        _bb_stream.git_add_commit_push_file (
            ".sops.yaml", 
            "chore: updating .sops.yaml",
            _app_settings.settings["bigbang"]["repository"]["branch"],
            _bb_stream.get_work_dir())

def configure_git(_app_settings, _bb_stream):

    log_line = "Configuring git"  

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)

        _bb_stream.sleep(2)

        _bb_stream.git_store_credentials(
            _app_settings.settings["credentials"]["github_user"], 
            _app_settings.settings["credentials"]["github_pat"]
        )

        git_global_user  = 'DSOP Builder'
        git_global_email ='no-reply@dsopbuilder.com'

        logger.debug (f"setting git credentials - {git_global_user}, {git_global_email}") 
        _bb_stream.git_config_global_user( git_global_user, git_global_email )        

        branch = _app_settings.settings["bigbang"]["repository"]["branch"]
        logger.debug (f"switching to branch - {branch}")
        _bb_stream.git_checkout_branch (branch, _bb_stream.get_project_dir())

def create_istio_certs_and_keys(_app_settings, _bb_stream):
    
    log_line = "Creating certs and keys for ISTIO"   
    
    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)

        _bb_stream.sleep(2)

        _bb_stream.generate_root_key_and_cert()
        _bb_stream.generate_domain_key_and_cert(domain=_app_settings.settings["bigbang"]["hostname"])

def install_bigbang (_bb_stream):
    log_line = "Installing Big Bang"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        _bb_stream.exec_kubectl_cmd(f"apply -f {_bb_stream.get_project_dir()}/bigbang.yaml")

def install_flux (_app_settings, _bb_stream):
    log_line = "Installing Flux"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        _bb_stream.install_flux ( 
            _app_settings.settings['credentials']['ironbank_user'],
            _app_settings.settings['credentials']['ironbank_pat'],
            "bigbang@bigbang.dev"
        )

        _bb_stream.exec_kubectl_cmd(f"delete netpol -n flux-system allow-scraping")

def prepare_kubernetes (_app_settings, _bb_stream):
    log_line = "Preparing Kubernetes"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        namespace = _app_settings.settings['bigbang']['namespace']
        _bb_stream.exec_kubectl_cmd (f"create namespace {namespace}")
       # _bb_stream.exec_kubectl_cmd (f"create namespace flux-system")

        #ib_user = _app_settings.settings['credentials']['ironbank_user']
        #ib_pat  = _app_settings.settings['credentials']['ironbank_pat']
        gh_user = _app_settings.settings['credentials']['github_user']
        gh_pat = _app_settings.settings['credentials']['github_pat']
        _bb_stream.exec_kubectl_cmd (f"create secret generic sops-gpg -n {namespace} --from-file=bigbangkey.asc")
        #_bb_stream.exec_kubectl_cmd (f"create secret docker-registry private-registry --docker-server=registry1.dso.mil --docker-username={ib_user} --docker-password={ib_pat} -n flux-system")
        _bb_stream.exec_kubectl_cmd (f"create secret generic private-git --from-literal=username={gh_user} --from-literal=password={gh_pat} -n bigbang")

def update_bigbang_yaml(_app_settings, _bb_stream):
    log_line = "Updating bigbang.yaml"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)

        tokens = {
            "__CHANGE_ME_REPO_URL__" : _app_settings.settings["bigbang"]["repository"]["url"],
            "__CHANGE_ME_REPO_BRANCH__": _app_settings.settings["bigbang"]["repository"]["branch"],
        }

        _bb_stream.sleep(2)

        template_file = f"{_bb_stream.get_project_dir()}/bigbang.yaml.save"
        out_file = f"{_bb_stream.get_project_dir()}/bigbang.yaml"

        create_file_from_template (template_file, out_file, tokens)        
        cout_success ("Successfully applied changes to bigbang.yaml")

        _bb_stream.git_add_commit_push_file (
            "bigbang.yaml", 
            "chore: updating bigbang.yaml",
            _app_settings.settings["bigbang"]["repository"]["branch"],
            _bb_stream.get_project_dir())

        cout_success ("Successfully pushed updates to bigbang.yaml")

def update_secrets_yaml (_app_settings, _bb_stream):
    
    log_line = "Updating secrets.enc.yaml"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)
    
        secret_tokens = {
                "${IRON_BANK_USER}": _app_settings.settings["credentials"]["ironbank_user"],
                "${IRON_BANK_PAT}" : _app_settings.settings["credentials"]["ironbank_pat"]
            }
                
        secrets_yaml_template = f"{_bb_stream.get_scripts_dir()}/secrets.enc.yaml.template"
        secrets_yaml_file = f"{_bb_stream.get_work_dir()}/base/secrets.enc.yaml"
        create_file_from_template (secrets_yaml_template, secrets_yaml_file, secret_tokens)
        _bb_stream.sops_encrypt ("secrets.enc.yaml", f"{_bb_stream.get_work_dir()}/base")
        cout_success ("secrets.enc.yaml file created")

        _bb_stream.git_add_commit_push_file (
                "secrets.enc.yaml", 
                "chore: updating secrets.enc.yaml",
                _app_settings.settings["bigbang"]["repository"]["branch"],
                f"{_bb_stream.get_work_dir()}/base")

def update_istio_yaml (_app_settings, _bb_stream):
    log_line = "Updating istio-gw-cert.enc.yaml"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)
    
        istio_key, istio_crt = _bb_stream.get_domain_key_and_cert_base64(_app_settings.settings["bigbang"]["hostname"])
        istio_tokens = {
            "${ISTIO_GW_KEY}": istio_key,
            "${ISTIO_GW_CRT}": istio_crt
        }

        istio_yaml_template = f"{_bb_stream.get_scripts_dir()}/istio-gw-cert.enc.yaml.template"
        istio_yaml_file = f"{_bb_stream.get_work_dir()}/base/istio-gw-cert.enc.yaml"
        create_file_from_template (istio_yaml_template, istio_yaml_file, istio_tokens)
        _bb_stream.sops_encrypt ("istio-gw-cert.enc.yaml", f"{_bb_stream.get_work_dir()}/base")
        cout_success("istio-gw-crt.enc.yaml file created")

        _bb_stream.git_add_commit_push_file (
            "istio-gw-cert.enc.yaml", 
            "chore: updating istio-gw-cert.enc.yaml",
            _app_settings.settings["bigbang"]["repository"]["branch"],
            f"{_bb_stream.get_work_dir()}/base")

def validate_settings_and_environment(_app_settings, _bb_stream):

    log_line = "Validating settings and verifying environment"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        #Ensure that app-settings are valid
        if(_app_settings.validate_bigbang() == False):
            exit(1)

        logger.debug("Verifying Kubernetes Cluster")
        settings.kubeversion()
        cout_success (f"Kubernetes cluster is ready!")
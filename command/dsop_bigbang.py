from re import template
from sqlite3 import Time
from util.streams import Stream
from util.bb_streams import BigBang_Stream
from appsettings import AppSettings
import pathlib
import util
from util.io import *
import os
#from rich.console import Console
import time
import sys
import logging
from rich import print
from rich.panel import Panel
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

_working_dir = "working"
_clone_bigbang_dir = "bigbang"

@app.command()
def deploy ():
    """
        Deploys BigBang to a Kubernetes Cluster in Azure. Requires Kubernetes config to be set before running.
    """

    Timed()

    _app_settings = AppSettings('./config/config-bigbang.json')
    _bb_stream   = BigBang_Stream(_clone_bigbang_dir, _working_dir, pathlib.Path().resolve(), project_dir='dev')

    print(Panel.fit("PyBuilder - The Pythonic Azure Big Bang Deployment Tool\nReuben Cleetus - reuben@cleet.us\nwith Tim Meyers - timothy.m.meyers@gmail.com (AKS & BB)"))


    #------- Validate settings; check Kubernetes ------------------------------

    validate_settings_and_environment(_app_settings)

    # ------- Create Git Repository -------------------------------------------

    configure_git(_app_settings, _bb_stream)   

    #------- Create GPG Encryption Key ----------------------------------------

    if bool(_app_settings.settings["bigbang"]["keys"]["create_keys"]) == True:
        create_istio_certs_and_keys(_app_settings, _bb_stream)

    create_gpg_keys_and_update_sops_yaml(_app_settings, _bb_stream)

    # ------- Add TLS Certificates --------------------------------------------
    # ------- Add Pull Credentials (done in same step) ------------------------

    update_secrets_yaml(_app_settings, _bb_stream)

    # ------- Configure for GitOps (Update bigbang.yaml) ----------------------

    update_bigbang_yaml(_app_settings, _bb_stream)      

    # ------- Deploy (Configure kubernetes cluster - namespaces, secrets) -----

    prepare_kubernetes (_app_settings, _bb_stream)
    
    if bool(_app_settings.settings["bigbang"]["flux"]["deploy_flux"]) == True:
        install_flux (_app_settings, _bb_stream)

    install_bigbang(_bb_stream)

    Timed()

    print_success()

@app.command()
def verify():
    """
        Verifies a BigBang deployment reconciliation. Requires Kubernetes config to be set before running.
    """

    _bb_stream   = BigBang_Stream(_clone_bigbang_dir, _working_dir, pathlib.Path().resolve(), project_dir='dev')
    
    command = f"get gitrepositories,ks,hr -A"
    
    _bb_stream.exec_kubectl_cmd(command)

def create_gpg_keys_and_update_sops_yaml(_app_settings:AppSettings, _bb_stream:BigBang_Stream):
    fingerprint = None
    
    log_line = "Get GPG key fingerprint"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        gpg_key_name =  _app_settings.settings["bigbang"]["keys"]["gpg_key_name"]
       
        fingerprint = _bb_stream.get_gpg_fingerprint (gpg_key_name, create_if_needed=True)
        _bb_stream.generate_gpg_secret_file(fingerprint)

        cout_success ("Success - Obtained gpg fingerprint")    

    log_line = "Updating .sops.yaml"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        tokens = {"FALSE_KEY_HERE": fingerprint}

        template_file = f"{_bb_stream.get_work_dir()}/.sops.yaml.template"
        out_file = f"{_bb_stream.get_work_dir()}/.sops.yaml"
        create_file_from_template (template_file, out_file, tokens) 

        _bb_stream.git_add_commit_push_file (
            ".sops.yaml", 
            "chore: updating .sops.yaml",
            _app_settings.settings["bigbang"]["repository"]["branch"],
            _bb_stream.get_work_dir())

def configure_git(_app_settings:AppSettings, _bb_stream:BigBang_Stream):

    log_line = "Configuring git"  

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)

        _bb_stream.sleep(2)

        _bb_stream.git_store_credentials(
            _app_settings.settings["credentials"]["github_user"], 
            _app_settings.settings["credentials"]["github_pat"]
        )

        _bb_stream.git_config_global_user( 
            username='DSOP Builder', 
            email='no-reply@dsopbuilder.com')        

        _bb_stream.git_config_origin (
            _app_settings.settings["bigbang"]["repository"]["url"],
            _bb_stream.get_project_dir())

        _bb_stream.git_checkout_branch (
            _app_settings.settings["bigbang"]["repository"]["branch"],
            _bb_stream.get_project_dir())

        cout_success (f"Successfully configured Git for GitOps")

def create_istio_certs_and_keys(_app_settings:AppSettings, _bb_stream:BigBang_Stream):
    
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

def install_flux (_app_settings:AppSettings, _bb_stream:BigBang_Stream):
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

def prepare_kubernetes (_app_settings:AppSettings, _bb_stream:BigBang_Stream):
    log_line = "Preparing Kubernetes"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)

        namespace = _app_settings.settings['bigbang']['namespace']
        ib_user = _app_settings.settings['credentials']['ironbank_user']
        ib_pat  = _app_settings.settings['credentials']['ironbank_pat']
        gh_user = _app_settings.settings['credentials']['github_user']
        gh_pat = _app_settings.settings['credentials']['github_pat']

        _bb_stream.exec_kubectl_cmd (f"create namespace {namespace}")
        _bb_stream.exec_kubectl_cmd (f"create secret generic sops-gpg -n {namespace} --from-file=bigbangkey.asc")

        _bb_stream.exec_kubectl_cmd (f"create namespace flux-system")
        _bb_stream.exec_kubectl_cmd (f"create secret docker-registry private-registry --docker-server=registry1.dso.mil --docker-username={ib_user} --docker-password={ib_pat} -n flux-system")
        
        _bb_stream.exec_kubectl_cmd (f"create secret generic private-git --from-literal=username={gh_user} --from-literal=password={gh_pat} -n bigbang")

def update_bigbang_yaml(_app_settings:AppSettings, _bb_stream:BigBang_Stream):
    log_line = "Updating bigbang.yaml"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)

        tokens = {
            "https://replace-with-your-git-repo.git" : _app_settings.settings["bigbang"]["repository"]["url"],
            "replace-with-your-branch": _app_settings.settings["bigbang"]["repository"]["branch"],
        }

        _bb_stream.sleep(2)

        template_file = f"{_bb_stream.get_project_dir()}/bigbang.yaml.template"
        out_file = f"{_bb_stream.get_project_dir()}/bigbang.yaml"

        create_file_from_template (template_file, out_file, tokens)        
        cout_success ("Successfully applied changes to bigbang.yaml")

        _bb_stream.git_add_commit_push_file (
            "bigbang.yaml", 
            "chore: updating bigbang.yaml",
            _app_settings.settings["bigbang"]["repository"]["branch"],
            _bb_stream.get_project_dir())

        _bb_stream.git_add_commit_push_file (
            "configmap.yaml", 
            "push initial configmap.yaml",
            _app_settings.settings["bigbang"]["repository"]["branch"],
            _bb_stream.get_project_dir())

        cout_success ("Successfully pushed updates to bigbang.yaml")

def update_secrets_yaml (_app_settings:AppSettings, _bb_stream:BigBang_Stream):
    
    log_line = "Updating secrets.enc.yaml"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)
        _bb_stream.sleep(2)
    
        istio_key, istio_crt = _bb_stream.get_domain_key_and_cert_base64(_app_settings.settings["bigbang"]["hostname"])
        
        secret_tokens = {
                "${IRON_BANK_USER}": _app_settings.settings["credentials"]["ironbank_user"],
                "${IRON_BANK_PAT}" : _app_settings.settings["credentials"]["ironbank_pat"],
                "${ISTIO_GW_KEY}": istio_key,
                "${ISTIO_GW_CRT}": istio_crt
            }
                
        #secrets_yaml_template = f"{_bb_stream.get_scripts_dir()}/secrets.enc.yaml.template"
        #secrets_yaml_file = f"{_bb_stream.get_work_dir()}/base/secrets.enc.yaml"       
        
        if bool(_app_settings.settings["bigbang"]["keys"]["create_keys"]) == True:
            secrets_yaml_template = f"{_bb_stream.get_work_dir()}/base/bigbang-dev-cert.yaml.template" 
        else: 
            secrets_yaml_template = f"{_bb_stream.get_work_dir()}/base/bigbang-dev-cert.yaml.default.template" 

        secrets_yaml_template = f"{_bb_stream.get_work_dir()}/base/bigbang-dev-cert.yaml.template"  
        secrets_yaml_file = f"{_bb_stream.get_work_dir()}/base/secrets.enc.yaml" 
        create_file_from_template (secrets_yaml_template, secrets_yaml_file, secret_tokens)
        create_file_from_template (secrets_yaml_template, f"{secrets_yaml_file}.debug", secret_tokens)
        _bb_stream.sops_encrypt ("secrets.enc.yaml", f"{_bb_stream.get_work_dir()}/base")
        cout_success ("secrets.enc.yaml file created")

        _bb_stream.git_add_commit_push_file (           
            "secrets.enc.yaml", 
            "chore: updating secrets.enc.yaml",
            _app_settings.settings["bigbang"]["repository"]["branch"],
            f"{_bb_stream.get_work_dir()}/base")

def update_istio_yaml (_app_settings:AppSettings, _bb_stream:BigBang_Stream):
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

def validate_settings_and_environment(_app_settings:AppSettings):

    log_line = "Validating settings and verifying environment"

    with console.status (f"{log_line}:\n"):
        logger.debug(log_line)

        #Ensure that app-settings are valid
        if(_app_settings.validate_bigbang() == False):
            exit(1)

        logger.debug("Verifying Kubernetes Cluster")
        settings.kubeversion()
        cout_success (f"Kubernetes cluster is ready!")

def print_success ():
    cout_success("Deployment Completed!")
    cout_success("Next Steps:")
    cout_success("1. Be sure to save off the *.crt and *.key files in working/bigbang/dev so you can import them into your browser and access Big Bang")
    cout_success("2. Monitor / Verify Big Bang reconciliation by running: python3 main.py bb verify. This usually takes 10-20 minutes")
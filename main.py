from sqlite3 import Time
from util import streams
from appsettings import AppSettings
import click
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
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
console = Console()



_app = None
_working_dir = "working"
_clone_dsop_rke2_dir = "dsop_rke2"
_stream = streams.Stream(_clone_dsop_rke2_dir, _working_dir, pathlib.Path().resolve())
_terraform_file = f"{str(pathlib.Path().resolve())}/{_working_dir}/{_clone_dsop_rke2_dir}/example/terraform.tfvars"

@click.command()
@click.option('--config', default="", help="Path and Filename of Custom Cofig File Location. If not provided, './config/config.json' is assumed")
@click.option('--settings', default="n", help="Print app config settings (these configure Azure Cloud Login and Terraform)")
@click.option('--deploy', default="n", help="Only run local splicing of Terraform values. If 'y', the Terrform deployment is also performed (default)")
@click.option('--destroy', default="n", help="Destroy the resources created by Terraform. If 'y', Destroy. USE WITH CARE!")
def main(config:str = "", settings:str="", deploy:str="n", destroy:str="n"):
    print(Panel.fit("PyBuilder - The Pythonic Azure Big Bang Deployment Tool\nReuben Cleetus - reuben@cleet.us"))
    Timed()
    if config.strip() == "" : _app = AppSettings()
    if settings.strip() != "n":
        _app.print_settings_json()
        sys.exit()
    if destroy.strip() == "y":
        _stream.do_terraform_destroy()
        sys.exit()

    if bool(_app.settings["custom_vnet_settings"]["vnet_customize"]) == False:
        #No VNet Customization
        if os.path.isdir(f"{str(pathlib.Path().resolve())}/{_working_dir}") == False: _stream.Do_No_VNet_Customization()
        _stream.do_rename_terraform_file()
        with console.status("Applying Terraform settings...", spinner="earth"):
            logger.debug("Applying config settings")
            splice_file_token(_terraform_file,"cluster_name", _app.settings["general"]["cluster_name"])
            splice_file_token(_terraform_file, "cloud", _app.settings["general"]["cloud"])
            splice_file_token(_terraform_file, "location", _app.settings["general"]["location"])
            splice_file_token(_terraform_file, "server_public_ip", _app.settings["connectivity"]["server_public_ip"])
            splice_file_token(_terraform_file, "server_open_ssh_public", _app.settings["connectivity"]["server_open_ssh_public"])
            _stream._cout_success("Completed Terraform Token splicing!")

        if deploy.strip() == "y":
            with console.status("Initializing Azure-CLI login...", spinner="earth"):
                logger.debug("Initializing Azure Cloud")
                _stream.do_cloud_login()
                _stream._cout_success("Azure Login Completed.")
            with console.status("Initializing Terraform...", spinner="earth"):
                logger.debug("Initializing Terraform")
                _stream._run_terraform_init()
                _stream._cout_success("Terraform Init Completed!")
            with console.status("Running Terraform... This may take a while: ", spinner="earth"):
                logger.debug("Running Terraform")
                _stream._run_terraform()
                _stream._cout_success("Deployment Completed!")
    else:
        #VNet Customization
        pass
    Timed()



if __name__ == '__main__':
    main()
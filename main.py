from sqlite3 import Time
from util import streams
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
import command.dsop_rke2 as dsop_rke2
import command.dsop_bigbang as dsop_bigbang

app = typer.Typer()
app.add_typer(settings.app, name="settings", help="Show and configure Settings information")
app.add_typer(dsop_rke2.app, name="rke2", help="Apply settings and build a Rancher RKE2 Cluster in Azure")
app.add_typer(dsop_bigbang.app, name="bb", help="Apply settings and deploy Big Bang to a K8S Cluster in Azure")


log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
console = Console()



_app_settings = None
_working_dir = "working"
_clone_dsop_rke2_dir = "dsop_rke2"
_stream = None
_terraform_file = f"{str(pathlib.Path().resolve())}/{_working_dir}/{_clone_dsop_rke2_dir}/example/terraform.tfvars"


@app.command()
def main():
    """
        Deprecated. Please use the rke2 or aks commands
    """
    print(Panel.fit("PyBuilder - The Pythonic Azure Big Bang Deployment Tool\nReuben Cleetus - reuben@cleet.us"))

    cout_success("run main.py --help for options")
    

if __name__ == '__main__':
    #typer.run(apply)
    app()
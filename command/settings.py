import typer
from appsettings import AppSettings
from util import io
from util.streams import Stream
import json
import subprocess
from rich.console import Console
from rich.table import Table

stream = Stream()
console = Console()
app = typer.Typer()
app_settings = None
AZ_GET_CLOUD_LIST = "az cloud list -o json"
AZ_STATUS = "az account show"
@app.command()
def list():
    """
    Lists the current configuration settings (config.json)
    """
    app_settings = AppSettings()
    app_settings.print_settings_json()

@app.command()
def azaccount():
    """
    List the currently logged in account
    """
    try:
        doc = json.loads(subprocess.run([AZ_STATUS], check=False, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8'))
    except Exception as e:
        stream.cout_error("You're not logged in to Azure! Use 'azlogingov' to log in to Azure Government.")
        exit(1)
    #console.print_json(json.dumps(doc, indent=3))
    table = Table(title="Azure Cloud")
    table.add_column("Cloud Name", justify="left", style="white", no_wrap=True)
    table.add_column("Is Default", style="magenta")
    table.add_column("Tenant ID", style="white")
    table.add_column("User", style="white")
    cloudName = doc['environmentName']
    isDefault = str(doc['isDefault'])
    tenant = str(doc['tenantId'])
    user = str(doc["user"]['name'])
    table.add_row(cloudName, isDefault, tenant, user)
    console.print(table)

def is_logged_in():
    """
    Returns True if logged in to Azure, False otherwise
    """
    success = False
    try:
        doc = json.loads(subprocess.run([AZ_STATUS], check=False, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8'))
        success = True
    except Exception as e:
        ...
    return success

@app.command()
def azlist():
    """
    Lists all registered Clouds, Prints Cloud status
    """
    doc = json.loads(subprocess.run([AZ_GET_CLOUD_LIST], check=False, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8'))
    #console.print_json(json.dumps(doc, indent=3))
    table = Table(title="Azure Cloud")
    table.add_column("Cloud Name", justify="left", style="white", no_wrap=True)
    table.add_column("Is Active", style="magenta")
    is_not_usgovcloud = False
    is_check_for_gov_cloud_active = False   #set to True if Gov Cloud is required

    for n in range(len(doc)):
        cloudName = doc[n]['name']
        isActive = str(doc[n]['isActive'])
        if (is_check_for_gov_cloud_active):
            if (cloudName.lower() == "azureusgovernment" and isActive == 'False'):
                is_not_usgovcloud = True
        table.add_row(cloudName, isActive)
    if (is_not_usgovcloud):
        stream.cout_error("Switching to Azure US Government Cloud")
        if (stream.do_cloud_login()):
            stream.cout_success("Successfully logged in to Azure US Government")

    console.print(table)
    stream.cout_success("You're logged in to Azure! Please ensure that the correct Cloud is set.")

@app.command()
def azloginusgov():
    """
    Switches to USGovCloud
    """
    stream.do_cloud_login() #Set to switch to US Gov Cloud
    
    

if __name__ == '__main__':
    typer.run(azlogin)
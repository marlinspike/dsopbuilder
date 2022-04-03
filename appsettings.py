import json
from typing import DefaultDict, List
from collections import defaultdict
from util import streams
from rich.console import Console
console = Console()
import logging
import util.strings
from util import io

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class AppSettings:

    def __init__(self, config_file:str, raw_json_input=False):
        '''
            Creates the AppSettings object
            Parameters:
                config_file (str): relative path to file
                raw_json_input (bool): True if config_file is a raw json string; False if it's a file 
        '''
        self.appsettings_file = config_file
        self.raw_json_input = raw_json_input
        self.settings = {}
        self.read_appsettings()
        
    
    def print_settings_json(self):
        console.print_json(json.dumps(self.settings, indent=3))


    def read_appsettings(self):
        try:
            logger.debug("Read settings")
            if(self.raw_json_input == True):
                self.settings = json.loads(self.appsettings_file)
            else:
                with open(self.appsettings_file) as data_file:
                    appsettings = json.load(data_file)
                    self.settings = appsettings
            return self.settings
        except Exception as e:
            logger.error("Unable to open config.json")
            streams.cout_error(f"There was an error reading appsettings from: {self.appsettings_file}")
            streams.cout_error(e)

    def validate(self) -> bool:
        '''
            Validates the settings read from the config.json file
        '''
        is_valid = True
        rg = self.settings["general"]["cluster_name"]
        if (util.strings.validate_dsop_rg(rg) == False):
            is_valid = False
            io.cout_error("Invalid Cluster Name: Cluster names cannot contain special characters or '_'. Please edit config.json in the 'config' directory.")
        else:
            io.cout_success("Kubernetes settings are valid!")
            
        return is_valid

    def validate_bigbang(self) -> bool:
        '''
            Validates the settings read from the config-bigbang.json file
        '''

        is_valid = True

        if (self.settings["credentials"]["github_user"].__contains__("__")):
            is_valid = False
            io.cout_error("github_user not set in config-bigbang.json")
        if (self.settings["credentials"]["github_pat"].__contains__("__")):
            is_valid = False
            io.cout_error("github_pat not set in config-bigbang.json")
        if (self.settings["credentials"]["ironbank_user"].__contains__("__")):
            is_valid = False
            io.cout_error("ironbank_user not set in config-bigbang.json")
        if (self.settings["credentials"]["ironbank_pat"].__contains__("__")):
            is_valid = False
            io.cout_error("ironbank_pat not set in config-bigbang.json")
        if (self.settings["bigbang"]["repository"]["url"].__contains__("__")):
            is_valid = False
            io.cout_error("bigbang repository url not set in config-bigbang.json")
        if (self.settings["bigbang"]["repository"]["branch"].__contains__("__")):
            is_valid = False
            io.cout_error("bigbang repository branch not set in config-bigbang.json")

        if is_valid:
            io.cout_success("Big Bang settings in config-bigbang.json are valid!")

        return is_valid


if __name__ == '__main__':
    _app = AppSettings('./config/config-rke2.json')
    _app = AppSettings("{'general': {'cluster_name': 'dsop-rke2', 'cloud': 'AzureUSGovernmentCloud', 'location': 'usgovvirginia'}, 'cluster-size': {'server_instance_count': 1, 'agent_instance_count': 2, 'vm_size': 'Standard_D8_v3'}, 'connectivity': {'server_public_ip': 'true', 'server_open_ssh_public': 'true'}, 'custom_vnet_settings': {'vnet_customize': 0, 'use_external_vnet': 0, 'external_vnet_resource_group': 'rke2_rg', 'external_vnet_name': 'rke2-vnet', 'external_vnet_subnet_name': 'rke2-subnet'}, 'clone_dsop_repo_name': 'dsop_rke2'}", True)
    settings_dict = _app.read_appsettings()

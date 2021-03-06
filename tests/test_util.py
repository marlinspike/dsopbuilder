import pytest
from util.io import *
from rich.text import Text
from util.strings import *
from appsettings import AppSettings


def test_app_settings():
    app = AppSettings("{\"general\": {\"cluster_name\": \"dsop-rke2\", \"cloud\": \"AzureUSGovernmentCloud\", \"location\": \"usgovvirginia\"}, \"cluster-size\": {\"server_instance_count\": 1, \"agent_instance_count\": 2, \"vm_size\": \"Standard_D8_v3\"}, \"connectivity\": {\"server_public_ip\": \"true\", \"server_open_ssh_public\": \"true\"}, \"custom_vnet_settings\": {\"vnet_customize\": 0, \"use_external_vnet\": 0, \"external_vnet_resource_group\": \"rke2_rg\", \"external_vnet_name\": \"rke2-vnet\", \"external_vnet_subnet_name\": \"rke2-subnet\"}, \"clone_dsop_repo_name\": \"dsop_rke2\"}", True)

    assert(app != None)
    assert(app.settings.get("general").get("cluster_name") == 'dsop-rke2')
    assert(app.settings.get("clone_dsop_repo_name") == "dsop_rke2")

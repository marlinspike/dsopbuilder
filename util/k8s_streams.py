from re import sub
from sys import stdout
from rich import print as rprint
import os
import subprocess
from subprocess import PIPE, Popen, STDOUT
import pathlib
import logging
from util.io import *
from util.streams import Stream

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

_default_dsop_rke2_repo = "https://github.com/p1-dsop/dsop-rke2"

class K8S_Stream (Stream):
    def do_run_terraform(self):
        logger.debug("Running Terraform")
        self._run_terraform_init()
        self._run_terraform()

    def do_terraform_destroy(self):
        res = self._run_process(['terraform', f"-chdir={self.working_dir}/{self.repo_name}/example" ,'destroy'])

    def do_rename_terraform_file(self):
        dir = self.get_work_dir()
        logger.debug(f"Renaming TF_File: '{dir}/example/terraform.tfvars.sample' To '{dir}/example/terraform.tfvars'")
        if os.path.isfile(f"\"{dir}/example/terraform.tfvars\"") == False:
            logger.debug(f"Copying File: {dir}/example/terraform.tfvars.sample -> {dir}/example/terraform.tfvars")
            res = self._run_process(["cp", f"{dir}/example/terraform.tfvars.sample", f"{dir}/example/terraform.tfvars"]) 

    def do_vnet_customization():
        pass

    def Do_No_VNet_Customization(self ):
        dir = self.get_work_dir()
        self._clone_env_repo(False)

    def create_project_dir(self):
        """
            Creates the Project directory
        """
        res = self._run_process(['cp', '-R', f"{self.get_work_dir()}/example", f"{self.get_project_dir()}"],True)
        #cp -R <source_folder>/* <destination_folder>

    def _run_terraform_init(self):
        res = self._run_process(['terraform', f"-chdir={self.get_project_dir()}" ,'init'])      

    def _run_terraform(self):
        args = ['terraform', f"-chdir={self.get_project_dir()}", 'apply', '-auto-approve']
        res = self._run_process(args)
        self._copy_scripts()
        #res = self._run_process(['source', './fetch-kubeconfig.sh'], True, cwd=f"{self.get_project_dir()}", shell=False)
        #logger.debug(f"fetch-kubeconfig.sh: {res}\n")
        #res = self._run_process(['./fetch-ssh-key.sh'], True, cwd=f"{self.get_project_dir()}", shell=False) #--> Done with run_after_deploy.sh
        #logger.debug(f"fetch-ssh-key.sh: {res}\n")
        res = self._run_process(['./run_after_deploy.sh'], True, cwd=f"{self.get_project_dir()}" ,shell=True)
        logger.debug(f"run_after_deploy.sh: {res}\n")
        cout_success(res)
    
    def _copy_scripts(self):
        logger.debug(f"Copying script files to example directory")
        res = self._run_process(['cp', '/PyBuilder/working/dsop_rke2/scripts/fetch-kubeconfig.sh', '/PyBuilder/working/dsop_rke2/example'])
        res = self._run_process(['cp', '/PyBuilder/working/dsop_rke2/scripts/fetch-ssh-key.sh', '/PyBuilder/working/dsop_rke2/example'])  

if __name__ == '__main__':
    _stream = Stream()
    _stream.run_console()
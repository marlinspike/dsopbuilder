from re import sub
from sys import stdout
from rich import print as rprint
import os
import subprocess
from subprocess import PIPE, Popen, STDOUT
import pathlib
import logging
from util.io import *


log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

_default_dsop_rke2_repo = "https://github.com/p1-dsop/dsop-rke2"

class Stream:
    def __init__(self, repo_name:str="dsop_rke2", working_dir:str="working", base_dir:str="", project_dir:str=""):
        self.repo_name = repo_name
        self.working_dir = working_dir
        self.base_dir = base_dir
        self.project_dir = project_dir #Directory for the actual working files

    def do_run_terraform(self):
        logger.debug("Running Terraform")
        self._run_terraform_init()
        self._run_terraform()

    def cout(self, text: str):
        rprint(text)

    def get_work_dir(self) -> str:
        return f"{self.base_dir}/{self.working_dir}/{self.repo_name}"
    
    def get_project_dir(self) -> str:
        return f"{self.get_work_dir()}/{self.project_dir}"

    def get_scripts_dir(self) -> str:
        return f"{self.get_work_dir()}/scripts"
    
   
    def do_cloud_login(self) -> bool:
        logger.debug("Setting up Azure Cloud")
        success = False
        try:
            res = run_process(['az','cloud', 'set', '--name', 'AzureUSGovernment'])
            res = run_process(['az','login'])
            res = run_process(['az','cloud', 'list', '-o', 'table'])
            success = True
            cout_success("Successfully logged in to Azure US Government!")
        except Exception as e:
            logger.debug(f"Error logging in to Azure Cloud: {e}")
            cout_error(f"Error logging in to Azure Cloud {e}")
        return success

    def create_project_dir(self):
        """
            Creates the Project directory
        """
        res = run_process(['cp', '-R', f"{self.get_work_dir()}/example", f"{self.get_project_dir()}"],True)
        #cp -R <source_folder>/* <destination_folder>

    def _run_terraform_init(self):
        res = run_process(['terraform', f"-chdir={self.get_project_dir()}" ,'init'])      

    def _copy_scripts(self):
        logger.debug(f"Copying script files to example directory")
        try:
            res = run_process(['cp', '/PyBuilder/working/dsop_rke2/scripts/fetch-kubeconfig.sh', '/PyBuilder/working/dsop_rke2/example'])
            res = run_process(['cp', '/PyBuilder/working/dsop_rke2/scripts/fetch-ssh-key.sh', '/PyBuilder/working/dsop_rke2/example'])  
        except:
            ...

    def do_terraform_destroy(self):
        res = run_process(['terraform', f"-chdir={self.working_dir}/{self.repo_name}/example" ,'destroy'])

    def _run_terraform(self):
        args = ['terraform', f"-chdir={self.get_project_dir()}", 'apply', '-auto-approve']
        res = run_process(args)
        self._copy_scripts()
        #res = run_process(['source', './fetch-kubeconfig.sh'], True, cwd=f"{self.get_project_dir()}", shell=False)
        #logger.debug(f"fetch-kubeconfig.sh: {res}\n")
        #res = run_process(['./fetch-ssh-key.sh'], True, cwd=f"{self.get_project_dir()}", shell=False) #--> Done with run_after_deploy.sh
        #logger.debug(f"fetch-ssh-key.sh: {res}\n")
        res = run_process(['./run_after_deploy.sh'], True, cwd=f"{self.get_project_dir()}" ,shell=True)
        logger.debug(f"run_after_deploy.sh: {res}\n")
        cout_success(res)


    def Do_No_VNet_Customization(self ):
        dir = self.get_work_dir()
        self._clone_env_repo(False)


    def do_rename_terraform_file(self):
        dir = self.get_work_dir()
        logger.debug(f"Renaming TF_File: '{dir}/example/terraform.tfvars.sample' To '{dir}/example/terraform.tfvars'")
        if os.path.isfile(f"\"{dir}/example/terraform.tfvars\"") == False:
            logger.debug(f"Copying File: {dir}/example/terraform.tfvars.sample -> {dir}/example/terraform.tfvars")
            res = run_process(["cp", f"{dir}/example/terraform.tfvars.sample", f"{dir}/example/terraform.tfvars"]) 

    def _clone_env_repo(self, dsop_customization_required = False):
        #args = ['git', 'clone', _default_dsop_rke2_repo, f"{self.working_dir}/{self.repo_name}"]
        repo = f"https://github.com/p1-dsop/{self.repo_name}"
        args = ['git', 'clone', repo, f"{self.working_dir}/{self.repo_name}"]
        res = run_process(args)

    def run_console(self, ):
        res = run_process(['ls', '-l', '-a'],True)
        res = run_process(['echo', 'Hello', 'World!'],True)


    def git_store_credentials(self, user:str, pat:str,):
        
        command = "git config --global credential.helper store".split()

        try:       
            run_process(command)
            fout = open('/root/.git-credentials','wb')
            subprocess.run(['echo',f"https://{user}:{pat}@github.com"], stdout=fout)
            fout.close()
        except Exception as e:
            cout_error_and_exit (f"{e}")

    def git_config_global_user (self, username:str, email:str):
        run_process(['git','config','--global','user.name', username])
        run_process(['git','config','--global','user.email', email])
    
    def git_checkout_branch (self, branch:str, cwd:str=""):
        run_process (['git', 'checkout', '-b', branch], cwd=cwd)

    def git_add_commit_push_file (self, filename:str, message:str, branch:str, cwd:str=""):
        run_process (['git', 'add', filename],cwd=cwd)
        run_process (['git', 'commit', '-m', message],cwd=cwd)
        run_process (['git', 'push', '--set-upstream', 'origin', branch], cwd=cwd)

    def kube_version(self):
        command = "kubectl version".split()
        try: 
            res = subprocess.run (command, check=True, capture_output=True, encoding='UTF-8')
            cout_success (f"{res.stdout}")
        except Exception as e:
            cout_error_and_exit (f"Kubernetes cluster is not ready: {e}")

    def sleep(self, seconds:int):
        '''
        sleep, largely for debugging
        '''
        run_process(f"sleep {seconds}".split())

if __name__ == '__main__':
    _stream = Stream()
    _stream.run_console()
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
            res = self._run_process(['az','cloud', 'set', '--name', 'AzureUSGovernment'])
            res = self._run_process(['az','login'])
            res = self._run_process(['az','cloud', 'list', '-o', 'table'])
            success = True
        except Exception as e:
            logger.debug(f"Error logging in to Azure Cloud: {e}")
            cout_error(f"Error logging in to Azure Cloud {e}")
        return success

    def _clone_env_repo(self, dsop_customization_required: bool):
        args = ['git', 'clone', _default_dsop_rke2_repo, f"{self.working_dir}/{self.repo_name}"]
        res = self._run_process(args)

    def run_console(self, ):
        res = self._run_process(['ls', '-l', '-a'],True)
        res = self._run_process(['echo', 'Hello', 'World!'],True)

    def _run_process(self, args:list, read_output:bool=False, cwd:str="", shell:bool=False) -> str:
        logger.debug(f"Running process: {locals()}")
        if cwd.strip() == "":
            result = subprocess.run(args, capture_output=False, text=True)
            return None
        else:
            result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, shell=shell)
            return result.stdout

    def _run_processes_piped(self, in_args:list, out_args:list, cwd:str="", encoding:str=""):
        '''
            Simulates the process of running

            $ in_args | out_args
        '''

        logger.debug (f"Running piped processes: {locals()}")

        if cwd.strip() == "":
            cwd = '.'

        p1 = subprocess.Popen(in_args, stdout=subprocess.PIPE, cwd=cwd)
        p2 = subprocess.run(out_args,stdin=p1.stdout, cwd=cwd, capture_output=True, encoding='UTF-8', shell=True)

        #cout_success (f"{p2}")
        #cout_error (f"{p2.stdout}")

        return f"{p2.stdout}"

    def git_store_credentials(self, user:str, pat:str,):
        
        command = "git config --global credential.helper store".split()

        try:       
            self._run_process(command)
            fout = open('/root/.git-credentials','wb')
            subprocess.run(['echo',f"https://{user}:{pat}@github.com"], stdout=fout)
            fout.close()
        except Exception as e:
            cout_error_and_exit (f"{e}")

    def git_config_global_user (self, username:str, email:str):
        self._run_process(['git','config','--global','user.name', username])
        self._run_process(['git','config','--global','user.email', email])
    
    def git_checkout_branch (self, branch:str, cwd:str=""):
        self._run_process (['git', 'checkout', '-b', branch], cwd=cwd)

    def git_add_commit_push_file (self, filename:str, message:str, branch:str, cwd:str=""):
        self._run_process (['git', 'add', filename],cwd=cwd)
        self._run_process (['git', 'commit', '-m', message],cwd=cwd)
        self._run_process (['git', 'push', '--set-upstream', 'origin', branch], cwd=cwd)

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
        self._run_process(f"sleep {seconds}".split())

if __name__ == '__main__':
    _stream = Stream()
    _stream.run_console()
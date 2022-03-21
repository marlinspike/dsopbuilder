from re import sub
from sys import stdout
from rich import print as rprint
import os
import subprocess
from subprocess import PIPE
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

    def Do_No_VNet_Customization(self ):
        dir = self.get_work_dir()
        self._clone_env_repo(False)

    def create_proejct_dir(self):
        """
            Creates the Project directory
        """
        res = self._run_process(['cp', '-R', f"{self.get_work_dir()}/example", f"{self.get_project_dir()}"],True)
        #cp -R <source_folder>/* <destination_folder>


    
    def do_rename_terraform_file(self):
        dir = self.get_work_dir()
        logger.debug(f"Renaming TF_File: '{dir}/example/terraform.tfvars.sample' To '{dir}/example/terraform.tfvars'")
        if os.path.isfile(f"\"{dir}/example/terraform.tfvars\"") == False:
            logger.debug(f"Copying File: {dir}/example/terraform.tfvars.sample -> {dir}/example/terraform.tfvars")
            res = self._run_process(["cp", f"{dir}/example/terraform.tfvars.sample", f"{dir}/example/terraform.tfvars"]) 

    def do_terraform_destroy(self):
        res = self._run_process(['terraform', f"-chdir={self.working_dir}/{self.repo_name}/example" ,'destroy'])

    def do_vnet_customization():
        pass

    def do_cloud_login(self):
        logger.debug("Setting up Azure Cloud")
        success = False
        try:
            res = self._run_process(['az','cloud', 'set', '--name', 'AzureUSGovernment'])
            res = self._run_process(['az','login'])
            res = self._run_process(['az','cloud', 'list', '-o', 'table'])
            success = True
        except Exception as e:
            logger.debug(f"Error logging in to Azure Cloud: {e}")
            cout_error("Error logging in to Azure Cloud")
        return success

    def do_run_terraform(self):
        logger.debug("Running Terraform")
        self._run_terraform_init()
        self._run_terraform()

    def fetch_kubeconfig(self):
        logger.debug("Fetching kubeconfig")
        # self._run_process(['./run_after_deploy.sh'], cwd=self.get_project_dir(), shell=True)

    # ------------ Big Bang specific commands ---------------------

    def do_create_root_certs(self):

        logger.debug("Creating root certs")
        dir = self.get_project_dir()
        
        try: 
          self._run_process([f"{self.get_scripts_dir()}/create-root-cert.sh"], cwd=dir)
          cout_success("Successfully created root certs!")
        except Exception as e:
          logger.debug(f"Error generating root certs: {e}")
          cout_error("Error generating root certs")

    def do_create_domain_certs(self, hostname:str):
        
        logger.debug("Creating domain certs")
        dir = self.get_project_dir()

        try:
          self._run_process([f"{self.get_scripts_dir()}/create-domain-cert.sh", hostname], cwd=dir)
          cout_success(f"Successfully created domain certs for <{hostname}>")
        except Exception as e:
          logger.debug(f"Error generating domain certs: {e}")
          cout_error("Error generating domain certs")

    def do_upload_domain_certs(self, hostname:str, kv_name:str):

        logger.debug("Uploading domain certs")

        # cat $HOSTNAME.crt | base64 -w0

        #argscat = [ "cat", f"{hostname}.crt"]

        #cat_res = self._run_process(argscat ,shell=True, read_output=True)
        #cert_res = self._run_process(["base64", "-w0", cat_res],shell=True)
        
        #self.cout(cert_res)

        # az keyvault secret set --name istio-gw-crt --vault-name $KV_NAME --encoding base64 --value "$ISTIO_GW_CRT"
        
        args = [
            'az','keyvault','secret','set',
            '--name', 'istio-gw-crt',
            '--vault-name', kv_name,
            '--encoding', 'base64', 
            '--value', ''
        ]

    
    def do_reset_bigbang_yaml(self):
        logger.debug("Resetting bigbang.yaml file ")
        dir = self.get_work_dir()

        try:
            self._run_process([f"{self.get_scripts_dir()}/reset.sh"], cwd=dir)
        except Exception as e:
          logger.debug(f"Error resetting bigbang.yaml: {e}")

    def do_update_bigbang_yaml(self, repository:str, branch:str):
        logger.debug("Updating bigbang.yaml file with repository information")
        dir = self.get_work_dir()

        try:
            self._run_process([f"{self.get_scripts_dir()}/update-bigbang-yaml.sh",'dev',repository,branch], cwd=dir)
            cout_success("Successfully updated bigbang.yaml")
        except Exception as e:
          logger.debug(f"Error updating bigbang.yaml: {e}")
          cout_error("Error updating bigbang.yaml")

    def store_git_credentials(self,  user:str, pat:str,):

        self._run_process (['git','config','--global','credential.helper','store'])

        fout = open('/root/.git-credentials','wb')
        subprocess.run(['echo',f"https://{user}:{pat}@github.com"], stdout=fout)


    def do_push_bigbang_yaml(self, repository:str, branch:str ):
        logger.debug("Pushing bigbang.yaml changes")
        dir = self.get_project_dir()

        try: 
            self._run_process (['git','config','--global','user.name','DSOP Builder'])
            self._run_process (['git','config','--global','user.email','no-reply@dsopbuilder.com'])
            self._run_process (['git', 'checkout', '-b', branch], cwd=dir)
            self._run_process (['git', 'add', 'bigbang.yaml'],cwd=dir)
            self._run_process (['git', 'commit', '-m', 'chore: updated bigbang.yaml'],cwd=dir)
            self._run_process (['git', 'push', '--set-upstream', 'origin', branch],cwd=dir)
        except Exception as e:
            logger.debug(f"Error pushing bigbang.yaml: {e}")
            cout_error(f"Error pushing bigbang.yaml: {e}")

    def do_create_secrets_sh(self, gh_user:str, gh_pat:str, ib_user:str, ib_pat:str, hostname:str):
        logger.debug("Creating secrets.sh")

        # cat $HOSTNAME.crt | base64 -w0
        istio_gw_crt = self._run_processes_piped (
            ['cat', f"{hostname}.crt"],
            ['base64', '-w0'],
            self.get_project_dir()
        )

        istio_gw_key = self._run_processes_piped (
            ['cat', f"{hostname}.key"],
            ['base64', '-w0'],
            self.get_project_dir(),
        )

        fout = open(f"{self.get_scripts_dir()}/secrets.sh", "wb")
        subprocess.run(['echo',f"export IRON_BANK_USER=\"{ib_user}\""], stdout=fout)
        subprocess.run(['echo',f"export IRON_BANK_PAT=\"{ib_pat}\""], stdout=fout)
        subprocess.run(['echo',f"export AZDO_USER=\"{gh_user}\""], stdout=fout)
        subprocess.run(['echo',f"export AZDO_PASSWORD=\"{gh_pat}\""], stdout=fout)
        subprocess.run(['echo',f"export ISTIO_GW_CRT=\"{istio_gw_crt}\""], stdout=fout)
        subprocess.run(['echo',f"export ISTIO_GW_KEY=\"{istio_gw_key}\""], stdout=fout)
        fout.close()

    def do_set_deploy_vars(self, kubeconfig_file:str=""):
        dir = self.get_scripts_dir()
        fout = open(f"{dir}/deploy-vars.sh", "wb")

        subprocess.run(['grep', '-v', 'USE_KEYVAULT_CERT', 'deploy-vars.sh.sample'], cwd=dir, stdout=fout)
        subprocess.run(['echo', f"export USE_KEYVAULT_CERT=\"false\""],stdout=fout)

        if kubeconfig_file.strip() != "":
            subprocess.run(['echo', f"export KUBECONFIG=\"{kubeconfig_file}\""],stdout=fout)

        fout.close()

    def do_bigbang_deploy(self):
        dir = self.get_scripts_dir()
        # res = self._run_process(['./deploy.sh'], cwd=dir, shell=True, read_output=True)

        # logger.debug ( f"deploy.sh {res}")
        # cout_success ( f"{res}" )

    # -------------------------------------------------------------

    def _clone_env_repo(self, dsop_customization_required: bool):
        args = ['git', 'clone', _default_dsop_rke2_repo, f"{self.working_dir}/{self.repo_name}"]
        res = self._run_process(args)

    def run_console(self, ):
        res = self._run_process(['ls', '-l', '-a'],True)
        res = self._run_process(['echo', 'Hello', 'World!'],True)


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
        res = self._run_process(['cp', '/PyBuilder/working/dsop_rke2/scripts/fetch-kubeconfig.sh', '/PyBuilder/working/dsop_rke2/example'])
        res = self._run_process(['cp', '/PyBuilder/working/dsop_rke2/scripts/fetch-ssh-key.sh', '/PyBuilder/working/dsop_rke2/example'])
        logger.debug(f"Copying script files to example directory")
    
        

    def _run_process(self, args:list, read_output:bool=False, cwd:str="", shell:bool=False) -> str:
        logger.debug(f"Running process: {locals()}")
        if cwd.strip() == "":
            result = subprocess.run(args, capture_output=False, text=True)
            return None
        else:
            result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, shell=shell)
            return result.stdout

    def _run_processes_piped(self, in_args:list, out_args:list, cwd:str=""):
        '''
            Simulates the process of running

            $ in_args | out_args
        '''

        logger.debug (f"Running piped processes: {locals()}")

        p1 = subprocess.Popen(in_args, stdout=subprocess.PIPE, cwd=cwd)
        p2 = subprocess.run(out_args,stdin=p1.stdout, cwd=cwd, capture_output=True, shell=True)

        return p2.stdout

if __name__ == '__main__':
    _stream = Stream()
    _stream.run_console()
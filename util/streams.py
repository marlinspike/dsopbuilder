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

        cout_success (f"{p2}")
        cout_error (f"{p2.stdout}")

        return f"{p2.stdout}".replace('\n','')

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

class BigBang_Stream (Stream):

    def generate_root_key_and_cert (self):
        '''
        Generates openssl ca.key and ca.crt files in the BigBang project directory.
        '''

        logger.debug ("Generating root (CA) cert")
        pdir = self.get_project_dir()

        if os.path.isfile (f"{pdir}/ca.key"):
            cout_error_and_exit ("Certificate Authority files already exist! Exiting.")

        self._generate_private_key("ca.key", "2048", cwd=pdir)
        self._generate_root_certificate ("ca.key", "ca.crt", cwd=pdir)
        
        logger.debug ("Successfully created root (CA) cert")

        cout_success ("Successfully generated root keys and certificates!")

        cout_success (f"The following files have been written:")
        cout_success (f"\t- ca.crt is the public certificate that should be imported in your browser.")
        cout_success (f"\t- ca.key is the private key that will be used to generate domain certs.")

        cout_success (f"Next step: Import ca.crt in your browser")

    def generate_domain_key_and_cert (self, domain:str):
        '''
        Generate openssl <domain>.key and <domain>.crt files in the BigBang project directory.
        '''

        logger.debug (f"Generating domain cert for <{domain}>")
        pdir = self.get_project_dir()
        
        if os.path.isfile (f"{pdir}/ca.key") == False:
            cout_error_and_exit ("Certificate Authority files missing! Exiting.")

        self._generate_private_key(f"{domain}.key", "2048", cwd=pdir)
        self._generate_domain_signing_request (domain, cwd=pdir)
        self._generate_domain_extension_config (domain, cwd=pdir)
        self._generate_domain_signed_certificate (domain, cwd=pdir)
        self._domain_cert_file_cleanup (domain, cwd=pdir)

        logger.debug (f"Successfully created domain cert for <{domain}>")
        cout_success (f"\tYou can now use {domain}.key and {domain}.crt in your web server.")
        cout_success (f"\tDon't forget that you must import ca.crt in your browser to make it accept the certificate.")

    def get_domain_key_and_cert_base64 (self, hostname):
        '''
        Returns a tuple of of the key and cert file for <hostname> in base64 string.
        '''       

        istio_gw_key = self._run_processes_piped (
            ['cat', f"{hostname}.key"],
            ['base64', '-w0'],
            self.get_project_dir(),
        )

        istio_gw_crt = self._run_processes_piped (
            ['cat', f"{hostname}.crt"],
            ['base64', '-w0'],
            self.get_project_dir(),
        )

        return f"{istio_gw_key}", f"{istio_gw_crt}"

    def store_key_and_cert_in_akv(self):
        pass

    def get_gpg_fingerprint (self, gpg_key_name:str, create_if_needed:bool = False):
        '''
        Returns the gpg fingerprint for the provided key name. Optionally create the gpg key if it does not exist.

        Note: This command uses gpg-key-gen.sh script provided in the container. Could not get gpg to operate without user interaction when executing via PyBuilder app.
        '''
        
        if not self._gpg_key_name_exists(gpg_key_name):
            if create_if_needed:
                self._generate_gpg_key_complete(gpg_key_name)
            else:
                cout_error_and_exit (f"GPG Key {gpg_key_name} does not exist. Exiting")
        else:
            logger.info("gpg keys exist already. skipping creation.")

        fingerprint = self._get_gpg_fingerprint(gpg_key_name)
    
        return fingerprint

    def generate_gpg_secret_file (self, fingerprint:str):
        '''
        Generates the gpg secret file - this later becomes a secret in Kubernetes
        '''
        command = f"gpg --export-secret-key --armor {fingerprint}".split()
        
        fout = open(f"bigbangkey.asc", "w+")
        subprocess.run(command, stdout=fout)
        fout.close()

    def sops_encrypt(self, file:str, cwd:str=""):
        '''
        Encryptes provided filename in place using SOPS. Exits on error.
        '''
        command = f"sops --encrypt --in-place {file}".split()
        res = subprocess.run(command, cwd=cwd, capture_output=True, encoding='UTF-8')

        cout_success(f"{res.stdout}")

        if (res.returncode != 0):
            cout_error_and_exit(f"{res.stderr}")

    def exec_kubectl_cmd(self, cmd=str):
        '''
        kubectl passthrough. Executes an arbitrary kubectl command. 
        Requires kubeconfig to be set.
        Exits on Error code.
        '''
        command = f"kubectl {cmd}".split()
        res = subprocess.run(command, capture_output=True, encoding='UTF-8')

        cout_success(f"{res.stdout}")

        if (res.returncode != 0):
            cout_error_and_exit(f"{res.stderr}")

    def install_flux (self, ib_user:str, ib_pat:str, ib_email:str):
        '''
        Installs flux using the bigbang install_flux.sh script.
        '''
        command = f"./scripts/install_flux.sh --registry-username {ib_user} --registry-password {ib_pat} --registry-email {ib_email} -w 180".split()

        flux_dir = f"{self.get_scripts_dir()}/bigbang-for-flux"
        #print (flux_dir)
        #print (command)

        #res = subprocess.run(command, capture_output=True, encoding='UTF-8', cwd=flux_dir)
        res = subprocess.run(command, cwd=flux_dir)

#        cout_success(f"{res.stdout}")
#        cout_error(f"{res.stderr}")

    # --------------------------------

    def _generate_private_key (self, new_key_file:str="ca.key", key_len:str="2048", cwd:str=""):
        command = ["openssl", "genrsa", "-out", new_key_file, key_len]
        try:
            res = self._run_process(command, read_output=True, cwd=cwd)
            cout_success (res)
            cout_success (f"Success! _generate_private_key")
        except Exception as e:
            logger.debug(f"Error generating private key: {e}")
            cout_error_and_exit(f"Error generating private key: {e}")    

    def _generate_root_certificate (self, key_file:str="ca.key", new_cert_file:str="ca.crt", cwd:str=""):
        
        # openssl req -x509 -new -nodes -subj "/C=US/O=_Development CA/CN=Development certificates" -key ca.key -sha256 -days 3650 -out ca.crt

        command_front = f"openssl req -x509 -new -nodes -subj".split()
        command_mid   = "/C=US/O=_Development CA/CN=Development certificates"
        command_back  = f"-key {key_file} -sha256 -days 3650 -out {new_cert_file}".split()
        
        command = command_front + [command_mid] + command_back

        try:
            #subprocess.run(command, cwd=cwd)
            self._run_process(command, cwd=cwd)
            cout_success (f"Success! _generate_root_certificate")

        except Exception as e:
            logger.debug(f"Error _generate_root_certificate: {e}")
            cout_error_and_exit(f"Error _generate_root_certificate: {e}")

    def _generate_domain_signing_request (self, domain:str, cwd:str=""):
        
        command_front = f"openssl req -new -subj".split()
        command_mid   = f"/C=US/O=Local Development/CN={domain}"
        command_back  = f"-key {domain}.key -out {domain}.csr".split()

        # command = f"openssl req -new -subj \"/C=US/O=Local Development/CN={domain}\" -key \"{domain}.key\" -out \"{domain}.csr\"".split()       

        command = command_front + [command_mid] + command_back

        try:
            self._run_process(command, cwd=cwd)
            cout_success (f"Success! _generate_domain_signing_request") 

        except Exception as e:
            logger.debug(f"Error _generate_domain_signing_request: {e}")
            cout_error_and_exit(f"Error _generate_domain_signing_request: {e}")

    def _generate_domain_extension_config (self, domain:str, cwd:str=""):

        ext_string = (""
        "authorityKeyIdentifier=keyid,issuer\n"
        "basicConstraints=CA:FALSE\n" 
        "keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment\n"            
        "extendedKeyUsage = serverAuth, clientAuth\n"
        "subjectAltName = @alt_names\n"
        "[alt_names]\n"             
        f"DNS.1 = {domain}\n"
        f"DNS.2 = *.{domain}")

        try: 
            fout = open(f"{domain}.ext", "w+")
            subprocess.run(['echo',ext_string], stdout=fout)
            fout.close()
        except Exception as e:
            cout_error_and_exit (f"Error: _generate_domain_extension_config {e}")

    def _generate_domain_signed_certificate (self, domain:str, cwd:str=""):
        command_str = (""
        "openssl x509 -req "
        f"-in {domain}.csr -extfile {self.base_dir}/{domain}.ext "
        f"-CA ca.crt -CAkey ca.key -CAcreateserial -out {domain}.crt -days 365 -sha256")

        command = command_str.split()

        try:
            self._run_process(command, cwd=cwd)
            cout_success (f"Success! _generate_domain_signed_certificate")
        except Exception as e:
            logger.debug(f"Error _generate_domain_signed_certificate: {e}")
            cout_error_and_exit(f"Error _generate_domain_signed_certificate: {e}")

    def _domain_cert_file_cleanup (self, domain:str, cwd:str=""):
        command = f"rm -rf {self.get_project_dir()}/{domain}.csr {self.base_dir}/{domain}.ext".split()

        try:
            self._run_process(command, shell=True)
            cout_success (f"Success! _domain_cert_file_cleanup")  
        except Exception as e:
            logger.debug(f"Error _domain_cert_file_cleanup: {e}")
            cout_error (f"{command}")
            cout_error_and_exit(f"Error _domain_cert_file_cleanup: {e}")

    def _gpg_key_name_exists (self, gpg_key_name:str):
        command = f"gpg -K {gpg_key_name}".split()
        try:
            subprocess.run(command, check=True)
            return True
        except Exception as e:
            return False

    def _generate_gpg_key (self, gpg_key_name:str):
        gen_cmd = f"gpg --quick-generate --batch --passphrase '.' {gpg_key_name}".split()
        print (gen_cmd)
        self._run_process(gen_cmd)

    def _generate_gpg_key_complete (self, gpg_key_name:str):
        gen_cmd = f"./gpg-key-gen.sh {gpg_key_name}".split()
        self._run_process(gen_cmd, cwd=self.get_scripts_dir())


    def _get_gpg_fingerprint (self, gpg_key_name:str):
        gpg_get_key_cmd = f"gpg -K {gpg_key_name}".split()
        sed_cmd = f"sed -e 's/ *//;2q;d;'"

        fingerprint = self._run_processes_piped (gpg_get_key_cmd, sed_cmd, encoding='UTF-8')
        #print (f"{fingerprint}")
        return fingerprint.strip()

    def _gpg_quick_add_fingerprint (self, fingerprint:str):
        command = f"gpg --quick-add-key --batch --yes --no-tty --passphrase '.' {fingerprint} rsa4096 encr".split()
        self._run_process(command)

    

    # -----------------------------------------------------------


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

if __name__ == '__main__':
    _stream = Stream()
    _stream.run_console()
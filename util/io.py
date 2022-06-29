import pathlib
import os
import logging
from timeit import default_timer as timer
from decimal import Decimal
from rich import print as rprint
from rich.text import Text
from rich.console import Console
import subprocess

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='../app.log', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
start:float = 0.0
end:float = 0.0

def splice_file_token(filename:str, key:str, new_value:str):
    '''
        Replaces the value for the key specified with the new_value passed, in the filename given.
    '''
    logger.debug(f"Splicing file: {locals()}")
    lines = None
    with open(filename, 'r') as fil:
        lines = fil.readlines()

    for i, line in enumerate(lines):
        if key in line.strip():
            lines[i] = f"{key} = \"{new_value}\"\n"

    with open(filename, 'w') as fil:
        fil.writelines(lines)

def splice_file_list(filename:str, key:str, new_value:list):
    '''
        Replaces the value for the key specified with the new_value list passed, in the filename given.
    '''

    logger.debug(f"Splicing file: {locals()}")
    lines = None
    with open(filename, 'r') as fil:
        lines = fil.readlines()

    for i, line in enumerate(lines):
        if key in line.strip():
            lines[i] = str(f"{key} = {new_value}\n").replace("\'", "\"")

    with open(filename, 'w') as fil:
        fil.writelines(lines)


def do_replace_tokens():
    splice_file_token("", "cluster_name")


def create_file_from_template(template:str, filename:str, tokens:dict):
    logger.debug(f"Creating {filename} from {template}")
    
    lines = None

    with open(template, 'r') as file_in:
        lines = file_in.readlines()

    for i, line in enumerate(lines):
        for key in tokens.keys():
            if line.find(key) != -1:
                lines[i] = lines[i].replace (key, tokens[key])

    with open(filename, 'w') as file_out:
        file_out.writelines(lines)


def run_process(args:list, read_output:bool=False, cwd:str="", shell:bool=False) -> str:
    logger.debug(f"Running process: {locals()}")
    if cwd.strip() == "":
        result = subprocess.run(args, capture_output=False, text=True)
        return None
    else:
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, shell=shell)
        return result.stdout

def run_processes_piped(in_args:list, out_args:list, cwd:str="", encoding:str=""):
    '''
        Simulates the process of running

        $ in_args | out_args
    '''
    logger.debug (f"Running piped processes: {locals()}")

    if cwd.strip() == "":
        cwd = '.'
    p1 = subprocess.Popen(in_args, stdout=subprocess.PIPE, cwd=cwd)
    p2 = subprocess.run(out_args,stdin=p1.stdout, cwd=cwd, capture_output=True, encoding='UTF-8', shell=True)
    return f"{p2.stdout}".replace('\n','')


if __name__ == '__main__':
    #splice_file_token("test.txt", "cluster_name", "cluster_name = \"reuben\"")
    print(pathlib.Path().resolve())


###
# Task Timer
def Timed():
    global start
    global end

    if(start == float(0.0)):
        start = timer()
    else:
        end = timer()
        print(f"\nCompleted in {round(Decimal(end - start),5) } seconds.")
        start = 0.0

def _cout(text: Text):
    '''
        Prints the specified Rich Text to Rich Console
    '''
    console = Console()
    console.print(text)

def cout_error(text: str):
    '''
        Outputs an error message in red
    '''
    rtext = Text(text)
    rtext.stylize("bold red")
    _cout(rtext)
    return rtext
    #rprint(f"[italic red]{text}[/italic red]")
    
def cout_error_and_exit(text: str, exit_code:int=-1):
    cout_error(f"\n{text}")
    exit(exit_code)

def cout_success( text: str):
    '''
        Outputs a success message in green
    '''
    rtext = Text(text)
    rtext.stylize("bold green")
    _cout(rtext)
    return rtext
    #rprint(f"[green]{text}[/green]")
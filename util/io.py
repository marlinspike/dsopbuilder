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


def run_process(self, args:list, read_output:bool=False, cwd:str="", shell:bool=False) -> str:
    '''
        Spawns and runs a process and runs the command specified in args
    '''
    logger.debug(f"Running process: {locals()}")
    if cwd.strip() == "":
        result = subprocess.run(args, capture_output=False, text=True)
        return None
    else:
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, shell=shell)
        return result.stdout

        

def do_replace_tokens():
    splice_file_token("", "cluster_name")


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
    

def cout_success( text: str):
    '''
        Outputs a success message in green
    '''
    rtext = Text(text)
    rtext.stylize("bold green")
    _cout(rtext)
    return rtext
    #rprint(f"[green]{text}[/green]")
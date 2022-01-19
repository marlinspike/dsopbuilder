
import pathlib
import os
import logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='../app.log', encoding='utf-8', level=logging.DEBUG, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def splice_file_token(filename:str, key:str, new_value:str):
    logger.debug(f"Splicing file: {locals()}")
    lines = None
    with open(filename, 'r') as fil:
        lines = fil.readlines()

    for i, line in enumerate(lines):
        if key in line.strip():
            lines[i] = f"{key} = \"{new_value}\"\n"

    with open(filename, 'w') as fil:
        fil.writelines(lines)


def do_replace_tokens():
    splice_file_token("", "cluster_name")


if __name__ == '__main__':
    #splice_file_token("test.txt", "cluster_name", "cluster_name = \"reuben\"")
    print(pathlib.Path().resolve())
from util.streams import Stream
import pytest
from util.io import *
from rich.text import Text
from util.strings import *
from appsettings import AppSettings

_working_dir = "working"
_clone_dsop_rke2_dir = "dsop-rke2"
project = "foo"
stream = Stream(_clone_dsop_rke2_dir, _working_dir, pathlib.Path().resolve(), project_dir=project)

def test_base_dir():
    base_dir = stream.get_work_dir()
    assert(base_dir != "")
    assert("dsop-rke2" in base_dir)

def test_project_dir():
    dir = stream.get_project_dir()
    assert("foo" in dir)
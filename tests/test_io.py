import pytest
from util.io import *
from rich.text import Text
from util.strings import *

def test_success():
    s:Text = cout_success("success")
    print(s)
    assert(str(type(s)) == "<class 'rich.text.Text'>")
    assert(str(s) == "success")

def test_valid_rg():
    s = "dsop-rke2"
    assert(validate_dsop_rg(s) == True)
    s = "dsop_rke2"
    assert(validate_dsop_rg(s) == False)

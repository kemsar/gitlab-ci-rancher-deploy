import os

import pytest
from cli_test_helpers import ArgvContext, EnvironContext
from click.testing import CliRunner

import ranchertool
from ranchertool import cli


# def test_entrypoint():
#     """
#     Is entrypoint script installed? (setup.py)
#     """
#     exit_status = os.system('ranchertool --help')
#     assert exit_status == 0


def test_cli():
    """
    Does CLI stop execution w/o a command argument?
    """
    with pytest.raises(SystemExit):
        ranchertool.cli.main()
        pytest.fail("CLI doesn't abort asking for a command argument")


def test_run_as_module():
    """
    Can this package be run as a Python module?
    """
    exit_status = os.system('python -m ranchertool --help')
    assert exit_status == 0


def test_fail():
    message_regex = "Error: Missing option '--rancher-url'."
    with ArgvContext('ranchertool'), pytest.raises(SystemExit):
        ranchertool.cli.main()
        pytest.fail("CLI didn't abort")


def test_fail_without_url():
    message_regex = "Error: Missing option '--rancher-url'."
    runner = CliRunner()
    with EnvironContext(RANCHER_URL=None), \
            ArgvContext('ranchertool'):
        result = runner.invoke(cli.main)
        assert result.exit_code == 2
        assert message_regex in result.output

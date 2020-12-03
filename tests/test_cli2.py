import os

import pytest
from cli_test_helpers import ArgvContext, EnvironContext
from click.testing import CliRunner

import ranchertool
from ranchertool import cli
from ranchertool import Logger


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
        cli.cli()
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
        ranchertool.cli.cli()
        pytest.fail("CLI didn't abort")


def test_fail_without_url():
    message_regex = "Usage:"
    runner = CliRunner()
    with EnvironContext(RANCHER_URL=None), \
            ArgvContext('ranchertool'):
        result = runner.invoke(cli.cli)
        log = Logger("DEBUG")
        log.info(result.output)
        assert result.exit_code == 0
        assert message_regex in result.output

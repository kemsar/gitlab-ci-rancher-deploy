from cli_test_helpers import EnvironContext
from click.testing import CliRunner

from helpers import Logger, LogLevel
from ranchertool import cli


def test_delete():
    logger = Logger(name='test_cli', log_level=LogLevel.DEBUG)
    runner = CliRunner()
    with EnvironContext(LOG_LEVEL='TRACE',
                        RANCHER_URL='https://rancher.dev.cu.edu',
                        RANCHER_ENV='ODIN-DEV',
                        RANCHER_STACK='odin-sandbox',
                        RANCHER_SERVICE='odin-api'):
        result = runner.invoke(cli.cli,
                               'delete'
                               )
        logger.info('OUTPUT:\r\n\r\n%s' % result.output)


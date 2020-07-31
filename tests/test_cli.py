from cli_test_helpers import EnvironContext
from click.testing import CliRunner

from helpers import Logger, LogLevel
from ranchertool import cli


def test_dev():
    message_regex = "Error: Missing option '--rancher-url'."
    logger = Logger(name='test_cli', log_level=LogLevel.DEBUG)
    runner = CliRunner()
    with EnvironContext(CI_PROJECT_NAMESPACE='odin',
                        CI_PROJECT_NAME='odin-api',
                        LOG_LEVEL='TRACE',
                        RANCHER_ENV='ODIN_DEV',
                        RANCHER_STACK='odin-sandbox',
                        # RANCHER_SERVICE='odin-portal',
                        IMAGE='registry.gitlab.dev.cu.edu/odin/odin-api:22'):
        result = runner.invoke(cli.main,
                               '--stack odin-sandbox '
                               '--create-stack '
                               '--create-service '
                               '--image registry.gitlab.dev.cu.edu/odin/odin-api:22 '
                               '--service-links "es-client=elasticsearch/es-client,kafka=kafka/kafka" '
                               '--variables "SPRING_PROFILES_ACTIVE=dev|jasypt.encryptor.password=${KEY}" '
                               '--labels "io.rancher.container.hostname_override=container_name,app=odin-api,owner=kevin.sarsen@cu.edu,commit=b6ee1ef2,traefik.enable=true,traefik.http.routers.feature--2-row-level-security.rule=Host(`https://feature--2-row-level-security.sbx.odin.dev.cu.edu`),traefik.http.routers.feature--2-row-level-security.service=feature--2-row-level-security,traefik.http.services.feature--2-row-level-security.loadbalancer.server.port=8081,traefik.domain=odin.dev.cu.edu,io.rancher.container.pull_image=always"')
        logger.info('OUTPUT:\r\n\r\n%s' % result.output)

# def test_all():
#     message_regex = "Error: Missing option '--rancher-url'."
#     logger = Logger(name='test_cli', log_level=LogLevel.DEBUG)
#     runner = CliRunner()
#     # THESE ARE CONFIGURED IN THE IDE RUN CONFIGURATION
#     # os.environ.get('RANCHER_ACCESS_KEY')
#     # os.environ.get('RANCHER_SECRET_KEY')
#     with EnvironContext(RANCHER_URL='https://rancher.dev.cu.edu',
#                         CI_PROJECT_NAMESPACE='odin',
#                         CI_PROJECT_NAME='odin-portal',
#                         LOG_LEVEL='DEBUG'):
#         result = runner.invoke(cli.main,
#                                '--stack odin-sandbox '
#                                '--create-stack '
#                                '--create-service '
#                                '--image registry.gitlab.dev.cu.edu/odin/odin-portal:1-ALPHA '
#                                '--service-link kafka kafka/kafka '
#                                '--service-links kafka=kafka/kafka,elasticsearch=elasticsearch/es-client '
#                                '--variable KAFKA_BROKERS_LIST kafka1:9093,kafka2:9093,kafka3:9093,kafka4:9093,kafka5:9093 '
#                                '--variables JAAS_CONFIG="org.apache.kafka.common.security.plain.PlainLoginModule '
#                                'required serviceName=\\"kafka\\" username=\\"admin\\" password=\\"A52b3Jmw7u\\";"|'
#                                'TOPIC_NAME=odin-enrollments|CONSUMER_GROUP_ID=test|KAFKA_SECURITY_PROTOCOL=SASL_SSL|'
#                                'KAFKA_SASL_MECHANISM=PLAIN|AUTO_OFFSET_RESET_CONFIG=latest|'
#                                'JNDI_FACTORY=weblogic.jndi.WLInitialContextFactory|URL=t3://osb-dev-01.dev.cu.edu:8011|'
#                                'JMS_TOPIC_CF=EventDrivenCF|JMS_TOPIC_NAME=OdinEnrollments '
#                                '--labels owner=kevin.sarsen@cu.edu,app=odin-portal-test')
#         logger.info('OUTPUT:\r\n\r\n%s' % result.output)
# assert message_regex in result.output

# def test_entrypoint():
#     """
#     Is entrypoint script installed? (setup.py)
#     """
#     exit_status = os.system('ranchlab --help')
#     assert exit_status == 0
#
#
# def test_cli():
#     """
#     Does CLI stop execution w/o a command argument?
#     """
#     with pytest.raises(SystemExit):
#         ranchlab.cli.main()
#         pytest.fail("CLI doesn't abort asking for a command argument")
#
#
# def test_run_as_module():
#     """
#     Can this package be run as a Python module?
#     """
#     exit_status = os.system('python -m ranchlab --help')
#     assert exit_status == 0
#
#
# def test_fail():
#     message_regex = "Error: Missing option '--rancher-url'."
#     with ArgvContext('ranchlab'), pytest.raises(SystemExit):
#         ranchlab.cli.main()
#         pytest.fail("CLI didn't abort")
#
#
# def test_fail_without_url():
#     message_regex = "Error: Missing option '--rancher-url'."
#     runner = CliRunner()
#     with EnvironContext(RANCHER_URL=None), \
#             ArgvContext('ranchlab'):
#         result = runner.invoke(cli.main)
#         assert result.exit_code == 2
#         assert message_regex in result.output

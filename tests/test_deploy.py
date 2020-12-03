from datetime import date, datetime

from cli_test_helpers import EnvironContext
from click.testing import CliRunner

from helpers import Logger, LogLevel
from ranchertool import cli


def test_deploy():
    logger = Logger(name='test_cli', log_level=LogLevel.DEBUG)
    runner = CliRunner()
    with EnvironContext(LOG_LEVEL='DEBUG',
                        RANCHER_URL='https://rancher.dev.cu.edu',
                        RANCHER_ENV='ODIN-DEV',
                        RANCHER_STACK='odin-sandbox',
                        RANCHER_SERVICE='odin-api',
                        IMAGE='registry.gitlab.dev.cu.edu/odin/odin-api:22'):
        current_timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        result = runner.invoke(cli.cli,
                               '--debug-http '
                               'deploy '
                               '--create-service '
                               '--image registry.gitlab.dev.cu.edu/odin/odin-api:22 '
                               '--service-links "es-client=elasticsearch/es-client|kafka=odin/odin-kafka" '
                               '--variables "SPRING_PROFILES_ACTIVE=dev" '
                               '--labels "io.rancher.container.hostname_override=container_name|app=odin-api|'
                               'owner=kevin.sarsen@cu.edu|maintainer=kevin.sarsen@cu.edu|timestamp=' +
                               current_timestamp + '|io.rancher.container.pull_image=always" '
                               '--secrets "test-token-one=TOKEN_ONE|test-token-two=TOKEN_2" '
                               )
        logger.info('OUTPUT:\r\n\r\n%s' % result.output)


# def test_delete():
#     logger = Logger(name='test_cli', log_level=LogLevel.DEBUG)
#     runner = CliRunner()
#     with EnvironContext(LOG_LEVEL='TRACE',
#                         RANCHER_ENV='ODIN-DEV',
#                         RANCHER_STACK='odin-sandbox',
#                         RANCHER_SERVICE='odin-api'):
#         result = runner.invoke(cli.cli,
#                                'delete'
#                                )
#         logger.info('OUTPUT:\r\n\r\n%s' % result.output)


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

import unittest
from logger import Logger, LogLevel

logger = Logger(LogLevel.DEBUG, "unittest-rancher")


class RancherTests(unittest.TestCase):

    def test_labels_processing(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'ranchlab',
            '',
            True,
            'v2-beta',
            logger.level)
        labels_str = 'label1=value1,label2=value2'
        labels_tup = [('label3', 'value3'), ('label4', 'This is my label'), ('label5', '"this is a test";')]
        rancher.set_labels(labels_str)
        rancher.set_labels(labels_tup)
        self.assertEqual(True, rancher.get_labels() is not None, "There should be labels defined on the Rancher object.")
        self.assertEqual(5, len(rancher.get_labels()), "There should be 2 labels defined on the Rancher object.")
        self.assertEqual('value1', rancher.get_labels()['label1'], "The first label should have value of value1")
        self.assertEqual('value3', rancher.get_labels()['label3'], "Label 3 added via tuple is wrong.")

    def test_string_variables_processing(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'ranchlab',
            '',
            True,
            'v2-beta',
            logger.level)
        variables_str = 'var1=val1|var2=val2 val3|var3="this is a test";'
        rancher.set_variables(variables_str)
        self.assertEqual(True, rancher.get_variables() is not None, 'There should be some variables')
        self.assertEqual(rancher.get_variables()['var1'], 'val1', 'variable 1 should have value of val1')
        self.assertEqual(rancher.get_variables()['var2'], 'val2 val3', "Variable 2 doesn't have the correct value.")
        self.assertEqual(rancher.get_variables()['var3'], '"this is a test";', "Variable 3 doesn't have the correct value.")

    def test_tuple_variables_processing(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'ranchlab',
            '',
            True,
            'v2-beta',
            logger.level)
        variables_tup = [('var4', 'val4'), ('var5', 'val5 val6'), ('var6', '"this is a test";')]
        rancher.set_variables(variables_tup)
        self.assertEqual(True, rancher.get_variables() is not None, 'There should be some variables')
        self.assertEqual(rancher.get_variables()['var4'], 'val4', 'variable 4 should have value of val4')
        self.assertEqual(rancher.get_variables()['var5'], 'val5 val6', "Variable 5 doesn't have the correct value.")
        self.assertEqual(rancher.get_variables()['var6'], '"this is a test";', "Variable 6 doesn't have the correct value.")

    def test_service_links_processing(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'ranchlab',
            '',
            True,
            'v2-beta',
            logger.level)
        service_links = 'kafka1=kafka/kafka1,kafka2=kafka/kafka2'

    def test_stack_exists(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'graphql',
            '',
            True,
            'v2-beta',
            logger.level)
        self.assertEqual(True, rancher.stack_exists(), "Didn't find a stack that should exist.")

    def test_stack_doesnt_exists(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'ranchlab',
            '',
            True,
            'v2-beta',
            logger.level)
        self.assertEqual(False, rancher.stack_exists(), "Something weird happened.")

    def test_create_stack(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'aaa-test-stack',
            'aaa-test-service',
            True,
            'v2-beta',
            logger.level)
        self.assertEqual(True, rancher.create_stack(), "Something weird happened.")
        self.assertEqual(True, rancher.stack_exists(), "Didn't find a stack that should exist.")

    def test_service_exists(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'graphql',
            'graphql',
            True,
            'v2-beta',
            logger.level)
        self.assertEqual(True, rancher.service_exists(), "Something weird happened.")

    def test_service_state(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'graphql',
            'graphql',
            True,
            'v2-beta',
            logger.level)
        self.assertEqual('active', rancher.get_service_state())

    def test_get_launchconfig(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'graphql',
            'graphql',
            True,
            'v2-beta',
            logger.level)
        self.assertIsNotNone(rancher.get_launch_config(), "Failed to get launch config")

    def test_do_upgrade(self):
        import os
        from helpers import RancherConnection
        rancher = RancherConnection(
            'https://rancher.dev.cu.edu',
            os.environ.get('RANCHER_ACCESS_KEY'),
            os.environ.get('RANCHER_SECRET_KEY'),
            'ODIN-DEV',
            'graphql',
            'sarsen-graphql',
            True,
            'v2-beta',
            LogLevel.TRACE)
        upgrade = {'inServiceStrategy': {
            'batchSize': 1,
            'intervalMillis': 2 * 1000,  # rancher expects milliseconds
            'startFirst': False,
            'startOnCreate': False,
            'launchConfig': {
            },
            'secondaryLaunchConfigs': []
        }}
        upgrade['inServiceStrategy']['launchConfig'] = rancher.get_launch_config()
        rancher.do_upgrade(upgrade)
        self.assertEqual(True,rancher.finish_upgrade())

if __name__ == '__main__':
    unittest.main()

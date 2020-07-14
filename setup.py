from setuptools import setup

setup(name='gitlab-ci-rancher-deploy',
      version='2.0',
      description='Tool to ease updating services in Rancher from your GitLab CI/CD pipeline, or anywhere.',
      url='https://github.com/kemsar/gitlab-ci-rancher-deploy',
      author='kemsar',
      license='MIT',
      packages=['ranchertool', 'ranchertool.helpers'],
      zip_safe=False,
      install_requires=[
          'wheel',
          'click',
          'requests',
          'colorama',
          'sakstig'
      ],
      tests_require=[
          'pytest',
          'cli_test_helpers'
      ],
      entry_points={
          'console_scripts': [
              'ranchertool = ranchertool.cli:main'
          ]
      }
      )

from setuptools import setup

setup(name='ranchlab',
      version='2.0',
      description='Command line tool to ease updating services in Rancher from your GitLab CI/CD pipeline',
      url='https://github.com/kemsar/rancher-gitlab-deploy',
      author='kemsar',
      license='MIT',
      packages=['ranchlab'],
      zip_safe=False,
      install_requires=[
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
              'ranchlab = ranchlab.cli:main']
      }
      )

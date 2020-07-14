# GitLab-CI Rancher Deploy

This project is a fork of Chris R.'s project, [rancher-gitlab-deploy](https://github.com/cdrx/rancher-gitlab-deploy). 
While his project hasn't had any updates in a couple of years, many thanks to him (and the other 
[contributors](https://github.com/cdrx/rancher-gitlab-deploy/graphs/contributors)) for laying the groundwork!

**GitLab-CI Rancher Deploy** is a tool for deploying Docker images built with GitLab CI into your Rancher 
infrastructure from your GitLab CI pipeline. It fits neatly into the GitLab CI/CD workflow and requires minimal 
configuration. In addition to deploying new services, it will also upgrade existing services as part of your CI 
workflow.

## Features

* Run either from local Python installation or from Docker container
* Create new Rancher Stacks
* Deploy new Rancher Services
* Update existing Rancher Services
* Compatible with Rancher API v1 and v2-beta
* Add labels to services
* Add environment labels to services
* Add service links to services

## Prerequisites

Before using **GitLab-CI Rancher Deploy**, there are a couple of prereqs that must be taken care of...

### Rancher Registry Access

In order to use **GitLab-CI Rancher Deploy** from your GitLab CI/CD pipelines, Rancher needs permission to access your
registry[^1]. 

First, you need to create an access token that can be used from Rancher to authenticate to the registry. One way to do 
that is to create a "Rancher" user in GitLab and create a Personal Access Token for that user with the "read_registry" 
scope. Then give the "Rancher" user "Developer" access to any project that you want to deploy to Rancher from.

The second step is to add the user to the desired Rancher environment. Login to the desired Rancher environment, select 
"INFRASTRUCTURE" from the top menu-bar, and select "Registries". Then click on the "Add Registry" button, select 
"Custom" from the available registry types and enter the GitLab registry URL and authentication information. Click 
"Create" and you should be good to go!

[^1]: This has *only* been tested with an on-prem GitLab registry. Outside of that, your mileage may vary.

### Rancher API Keys

Your Gitlab CI/CD pipeline needs to be able to authenticate to Rancher in order to perform its functions. To do that, it
needs a set of API keys. You create your API keys in Rancher by logging in to your target environment and, on the top 
menu bar, selecting "API > Keys".

It's important to note that Rancher supports two kinds of API keys: Environment and Account. You can use either with 
this tool, but **we recommend using Environment API keys**. If you *do* elect to use Account API keys and your account 
has access to more than one (1) environment, you'll need to specify the name of the environment with the `--environment` 
flag. For example, in your `.gitlab-ci.yml` file:

```yaml
my_deploy_job:
  stage: deploy
  script:
    - upgrade --environment MY-ENV
```

It's not necessary to specify the environment if using an Environment API key.

## Installation

**GitLab-CI Rancher Deploy** can either be run by installing the Python utility natively in your custom GitLab Runner 
or by building the Docker image and using that from your pipeline.

### Using the Docker Image

Build the Docker image using the included [Dockerfile](Dockerfile). You can then use the image in your pipeline:

```yaml
my_deploy_job:
    stage: deploy
    image: my_registry/gitlab-ci-rancher-deploy
    script:
      - upgrade --environment my_rancher_environment ...
```

### Installing with Python

If you are generating a custom Gitlab Runner, here's an example of adding **GitLab-CI Rancher Deploy** to your image:

```dockerfile
RUN apk --no-cache update && \
    apk --no-cache add \
        git \
        ncurses \
        python3 \
        python3-dev && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools click requests colorama && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    rm -rf /var/cache/* && \
    rm -rf /root/.cache/* && \
    git clone https://github.com/kemsar/gitlab-ci-rancher-deploy.git && \
    cd ./gitlab-ci-rancher-deploy && \
    git checkout master && \
    python ./setup.py install && \
```

## Configuration and Usage

For usage details, you can refer to the [--help output](HELP.md).

Please note that **GitLab-CI Rancher Deploy** will pull as much of its configuration as possible from environment 
variables, including both environment variables you set and those delivered by GitLab.

### Required Variables
At the very least, **GitLab-CI Rancher Deploy** requires three (3) variables be available:

* `RANCHER_URL` - The URL of your Rancher instance (eg `https://rancher.example.com`).
* `RANCHER_ACCESS_KEY` - A Rancher API Access Key (see [how to generate API keys](#rancher-api-keys) above)
* `RANCHER_SECRET_KEY` - A Rancher API Secret Key (see [how to generate API keys](#rancher-api-keys) above)

These variables can be set as either a) group- or project-level CI/CD secret variables, b) variables set in your CI/CD 
file (.gitlab-ci.yml) or c) values passed directly in the script.

### Basic Options
In addition to the required variables, you will probably want to provide basic options when running 
**GitLab-CI Rancher Deploy**. These include the target stack and service to upgrade, as well as the new or updated 
Docker image to use. These options are briefly described below, but for a full list of available options see the 
[Help](HELP.md) page or run the tool from the command line with the `--help` flag.

#### Rancher Stack and Service
By default, **GitLab-CI Rancher Deploy** will use the current project's GitLab group and project name as the stack and 
service name, respectively. For example, running an upgrade with the default settings in the project 
`http://gitlab.example.com/acme/webservice` will upgrade the service called `webservice` in the stack called `acme`.

If the names of your stack and service don't match your GitLab project, you can override the defaults with the 
`--stack` and `--service` flags:

```yaml
deploy:
  stage: deploy
  script:
    - upgrade --stack my-stack --service my-service
```

#### Docker Image
You can change the image (or :tag) used to deploy the upgraded containers with the `--new-image` option:

```yaml
deploy:
  stage: deploy
  script:
    - upgrade --new-image registry.example.com/acme/widget:1.2
```

#### Upgrade Strategy, etc.
The default upgrade strategy is to upgrade containers one at time, waiting 2s between each one. It will start new 
containers after shutting down existing ones, to avoid issues with multiple containers trying to bind to the same 
port on a host. It will wait for the upgrade to complete in Rancher, then mark it as finished. The default upgrade 
strategy can be overridden with various flags. Review the [Help](HELP.md) contents for all options.

## Examples

Using all defaults:

```yaml
image: docker:latest
services:
  - docker:dind

stages:
  - build
  - deploy

build:
  stage: build
  script:
    - docker login -u gitlab-ci-token -p $CI_BUILD_TOKEN registry.example.com
    - docker build -t registry.example.com/group/project .
    - docker push registry.example.com/group/project

deploy:
  stage: deploy
  variables:
    RANCHER_URL: https://rancher.example.com
    RANCHER_ACCESS_KEY: sdfg5tgsdf34wrd4q234fwe5y5wewrtg54we
    RANCHER_API_KEY: w45erfaedf4323awe55uyh6hts34
  script:
    - upgrade
```

A more complex example:

```yaml
deploy:
  stage: deploy
  variables:
    RANCHER_URL: https://rancher.example.com
    RANCHER_ACCESS_KEY: sdfg5tgsdf34wrd4q234fwe5y5wewrtg54we
    RANCHER_API_KEY: w45erfaedf4323awe55uyh6hts34
  script:
    - upgrade --environment production --stack acme --service web --new-image alpine:3.4 --no-finish-upgrade
```

## Troubleshooting: Limitations and Common Errors

### 422 Client Error: Unprocessable Entity

One possible reason for this error is discussed in [this issue report](https://github.com/rancher/rancher/issues/8129). 
In short, if you're trying to switch between global and fixed scale (either direction), you'll see this error. Check to 
see if you're setting the label `io.rancher.scheduler.global` to either `true` or `false` on an existing service.

### Error response from daemon: pull access denied for registry...repository does not exist or may require 'docker login'

This error is caused by a mis-configured or missing registry definition in Rancher. Review how to configure 
[Rancher Registry Access](#rancher-registry-access) and check to see if you have yours configured correctly.

## History
See the [Changelog](CHANGELOG.md).

## License
This project is licensed under the terms of the [MIT license](LICENSE).

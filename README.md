# RanchLab:  Deploy Docker Images to Rancher from GitLab CI/CD

**RanchLab** is a fork of Chris R.'s project, [rancher-gitlab-deploy](https://github.com/cdrx/rancher-gitlab-deploy). 
While his project hasn't had any updates in a couple of years, many thanks to him (and the other 
[contributors](https://github.com/cdrx/rancher-gitlab-deploy/graphs/contributors)) for laying the groundwork!

**RanchLab** is a tool for deploying containers built with GitLab CI onto your Rancher infrastructure.
It fits neatly into the GitLab CI/CD workflow and requires minimal configuration. It will upgrade existing 
services as part of your CI workflow.

## Installation


## Configuration
**RanchLab** will default as much of its configuration as possible from environment variables set by the GitLab 
CI runner.

### Required Variables
At the very least, **RanchLab** requires three (3) variables be available:

* `RANCHER_URL` : The URL of your Rancher instance (eg `https://rancher.example.com`).
* `RANCHER_ACCESS_KEY` : A Rancher API Access Key
* `RANCHER_SECRET_KEY` : A Rancher API Secret Key

These variables can be set as either a) group- or project-level CI/CD secret variables, b) variables set in your CI/CD 
file (.gitlab-ci.yml) or c) values passed directly in the script.

#### API Keys
Create your API keys in Rancher by logging in to your target environment and, on the top menu bar, selecting 
"API > Keys".

Rancher supports two kinds of API keys: Environment and Account. You can use either with this tool, but **we recommend 
using Environment API keys**. If you do elect to use Account API keys and your account has access to more than one (1) 
environment, you'll need to specify the name of the environment with the `--environment` flag. For example, in your 
`.gitlab-ci.yml` file:

```yaml
deploy:
  stage: deploy
  script:
    - upgrade --environment MY-ENV
```

### Basic Options
In addition to the required variables, you will probably want to provide basic options when running **RanchLab**. These 
include the target stack and service to upgrade, as well as the new or updated Docker image to use. These options 
are briefly described below, but for a full list of available options see the [Help](#help) section below.

#### Rancher Stack and Service
By default, **RanchLab** will use the GitLab group and project name as the stack and service name. For example, running 
an upgrade with the default settings in the project `http://gitlab.example.com/acme/webservice` will upgrade the 
service called `webservice` in the stack called `acme`.

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
strategy can be overridden with various flags. Review the [Help](#help) contents for all options.

## Usage

For usage details, refer to the [--help output](HELP).

### GitLab CI Example

Complete `.gitlab-ci.yml`:

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
  script:
    - upgrade
```

A more complex example:

```yaml
deploy:
  stage: deploy
  script:
    - upgrade --environment production --stack acme --service web --new-image alpine:3.4 --no-finish-upgrade
```

## History
See the [Changelog](CHANGELOG).

## License
This project is licensed under the terms of the [MIT license](LICENSE).

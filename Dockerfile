FROM python:3.8-alpine
ADD . /gitlab-ci-rancher-deploy
WORKDIR /gitlab-ci-rancher-deploy
RUN python /gitlab-ci-rancher-deploy/setup.py install
RUN ln -s /usr/local/bin/gitlab-ci-rancher-deploy /usr/local/bin/upgrade
CMD gitlab-ci-rancher-deploy

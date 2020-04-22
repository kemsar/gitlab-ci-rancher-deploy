#!/usr/bin/env python
import os, sys, subprocess
import click
import requests
import json
import logging
import contextlib


try:
    from http.client import HTTPConnection  # py3
except ImportError:
    from httplib import HTTPConnection  # py2

from time import sleep
from lib import RancherConnection


@click.command()
@click.option('--rancher-url', envvar='RANCHER_URL', required=True,
              help='The URL for your Rancher server.')
@click.option('--rancher-key', envvar='RANCHER_ACCESS_KEY', required=True,
              help="The environment or account API Access Key.")
@click.option('--rancher-secret', envvar='RANCHER_SECRET_KEY', required=True,
              help="The secret for the API Access Key.")
@click.option('--api-version', 'rancher_api_version', default='v2-beta', required=False,
              help="The API version to use. Rancher versions < 2 have API versions v1 and v2-beta. The default is "
                   "v2-beta.")
@click.option('--environment', 'rancher_environment_name', default=None,
              help="The name of the Rancher environment to operate in. " +
                   "This is only required if you are using an account API key instead of an environment API key.")
@click.option('--stack', 'rancher_stack_name', envvar='CI_PROJECT_NAMESPACE', default=None, required=True,
              help="The name of the target stack in Rancher. Defaults to the name of the GitLab project group as "
                   "defined in the CI_PROJECT_NAMESPACE environment variable.")
@click.option('--service', 'rancher_service_name', envvar='CI_PROJECT_NAME', default=None, required=True,
              help="The name of the service in Rancher to upgrade/create. Defaults to the name of the GitLab project "
                   "as defined in the CI_PROJECT_NAME environment variable.")
@click.option('--start-before-stopping/--no-start-before-stopping', default=False,
              help="Controls whether or not new containers should be started before the old ones are stopped. Defaults "
                   "to --no-start-before-stopping.")
@click.option('--batch-size', default=1,
              help="Sets the number of containers to upgrade simultaneously. Defaults to 1.")
@click.option('--batch-interval', default=2,
              help="Sets the number of seconds to wait between batches. Defaults to 2 seconds.")
@click.option('--timeout', default=5 * 60,
              help="Sets how many seconds to wait for Rancher to finish processing before assuming something went "
                   "wrong. Defaults to 300 seconds (5 mins). This setting is ignored if --no-wait is used.")
@click.option('--wait/--no-wait', 'wait_for_finish', default=True,
              help="Sets whether or not to wait for Rancher to finish processing the request. Defaults to --wait. If "
                   "--no-wait is used, --timeout is ignored.")
@click.option('--rollback/--no-rollback', 'rollback_on_error', default=False,
              help="Sets whether or not to roll back changes if an error occurs. Defaults to --no-rollback. Only valid "
                   "in conjunction with --wait.")
@click.option('--image', 'new_service_image', default=None,
              help="If specified, replaces the current service's image (and :tag) with the one specified.")
@click.option('--finish/--no-finish', 'finish_on_success', default=True,
              help="Sets whether or not to finish an upgrade when it completes. Defaults to --finish.")
@click.option('--sidekicks/--no-sidekicks', default=False,
              help="Sets whether or not to upgrade service sidekicks at the same time. Defaults to --no-sidekicks.")
@click.option('--new-sidekick-image', default=None, multiple=True,
              help="If specified, replaces the existing sidekick image (and :tag) with the specified one. This can be "
                   "defined more than once to upgrade multiple sidekicks. "
                   "Example: '--new-sidekick-image <sidekick-name> <new-image>'",
              type=(str, str))
@click.option('--create-stack/--no-create-stack', default=False,
              help="Sets whether or not to create the targeted Rancher stack if it doesn't exist. Defaults "
                   "to --no-create-stack.")
@click.option('--create-service/--no-create-service', default=False,
              help="Sets whether or not to create the targeted Rancher service if it doesn't exist. Defaults "
                   "to --no-create-service.")
@click.option('--labels', default=None,
              help="If specified, labels will be added to the service. Labels to be added should be provided as a "
                   "comma-delimited list of <label-name>=<label-value> pairs.")
@click.option('--label', default=None, multiple=True,
              help="Another way to add labels to a service. This one can be defined multiple times. "
                   "Example: '--label label1 value1 --label label2 value2'", type=(str, str))
@click.option('--variables', default=None,
              help="If specified, adds the passed list of environment variables to the service. The list of variables "
                   "should be a pipe-delimited (|) list of <key>=<value> pairs. "
                   "Example: '--variables var1=val1|var2=val2|var3=val3'.")
@click.option('--variable', default=None, multiple=True,
              help="Another way to add environment variables to a service. See --label for syntax.", type=(str, str))
@click.option('--service-links', default=None,
              help="If specified, adds the provided list of service links to the service. See --labels for syntax. "
                   "Example: '--service-links <local-name1>=<target-name1>,<local-name2>=<target-name2>'. Target "
                   "service name should be in the format of '<stack>/<service>'.")
@click.option('--service-link', default=None, multiple=True,
              help="Another way to add service links to a service. See --label for syntax.",
              type=(str, str))
@click.option('--debug/--no-debug', default=False,
              help="Sets whether or not HTTP debugging is enabled. Defaults to --no-debug.")
@click.option('--ssl-verify/--no-ssl-verify', default=True,
              help="Sets whether or not to perform certificate checks. Defaults to --ssl-verify. Use this to allow "
                   "connecting to a HTTPS Rancher server using an self-signed certificate")
def main(rancher_url, rancher_key, rancher_secret, rancher_api_version, rancher_environment_name, rancher_stack_name,
         rancher_service_name, new_service_image, batch_size, batch_interval,
         start_before_stopping, timeout, wait_for_finish, rollback_on_error, finish_on_success,
         sidekicks, new_sidekick_image, create_stack, create_service, labels, label, variables, variable,
         service_links, service_link, debug, ssl_verify):
    """
    Performs an in service upgrade of the service specified on the command line
    """

    rancher = RancherConnection()

    if debug:
        debug_requests_on()

    # split url to protocol and host
    if "://" not in rancher_url:
        bail("The Rancher URL doesn't look right. Please verify that it's a valid URL (i.e. https://my.rancher.com).")

    proto, host = rancher_url.split("://")
    rancher.api_endpoint = api = "%s://%s/%s" % (proto, host, rancher_api_version)
    rancher.stack_name = rancher_stack_name = rancher_stack_name.replace('.', '-')
    rancher.service_name = rancher_service_name = rancher_service_name.replace('.', '-')

    # session = requests.Session()

    # Set verify based on --ssl-verify/--no-ssl-verify option
    rancher.session.verify = ssl_verify

    # 0 -> Authenticate all future requests
    rancher.session.auth = (rancher_key, rancher_secret)

    # Check for labels and environment variables to set
    defined_labels = {}

    if labels is not None:
        labels_as_array = labels.split(',')

        for label_item in labels_as_array:
            key, value = label_item.split('=', 1)
            defined_labels[key] = value

    if label:
        for item in label:
            key = item[0]
            value = item[1]
            defined_labels[key] = value

    defined_environment_variables = {}

    if variables is not None:
        variables_as_array = variables.split('|')

        for variable_item in variables_as_array:
            key, value = variable_item.split('=', 1)
            defined_environment_variables[key] = value

    if variable:
        for item in variable:
            key = item[0]
            value = item[1]
            defined_environment_variables[key] = value

    # 1 -> Find the environment id in Rancher (aka "project")
    try:
        r = session.get("%s/projects?limit=1000" % api)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        bail("Unable to connect to Rancher at %s - is the URL and API key right?" % host)
    else:
        environments = r.json()['data']

    environment_id = None
    if rancher_environment_name is None:
        environment_id = environments[0]['id']
        environment_name = environments[0]['name']
    else:
        for e in environments:
            if e['id'].lower() == rancher_environment_name.lower() or e['name'].lower() == rancher_environment_name.lower():
                environment_id = e['id']
                environment_name = e['name']

    if not environment_id:
        if rancher_environment_name:
            bail(
                "The '%s' environment doesn't exist in Rancher, or your API credentials don't have access to it" % rancher_environment_name)
        else:
            bail("No environment in Rancher matches your request")

    # While we're here, let's define service links if provided
    defined_service_links = []
    # try:
    #     r = session.get("%s/projects/%s/services?limit=1000" % (
    #         api,
    #         environment_id
    #     ))
    #     r.raise_for_status()
    # except requests.exceptions.HTTPError:
    #     bail("Unable to fetch a list of stacks in the environment '%s'" % environment_name)
    # else:
    #     services = r.json()['data']

    if service_links is not None:
        service_links_as_array = service_links.split(',')

        for service_link_item in service_links_as_array:
            name, reference = service_link_item.split('=', 1)
            service_id = get_service_id_from_link_reference(reference, session, api, environment_id, environment_name)

            if service_id:
                defined_service_links.append({'name': name, 'serviceId': service_id})

    if service_link:
        for name, reference in service_link:
            service_id = get_service_id_from_link_reference(reference, session, api, environment_id, environment_name)

            if service_id:
                defined_service_links.append({'name': name, 'serviceId': service_id})

    # 2 -> Find the stack (aka "environment") in the environment (aka "project")

    try:
        r = session.get("%s/projects/%s/environments?limit=1000" % (
            api,
            environment_id
        ))
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        bail("Unable to fetch a list of stacks in the environment '%s'" % environment_name)
    else:
        stacks = r.json()['data']

    for s in stacks:

        if s['name'].lower() == rancher_stack_name.lower():
            rancher_stack_name = s
            break
    else:
        if create:
            new_stack = {
                'name': rancher_stack_name.lower()
            }
            try:
                msg("Creating stack %s in environment %s..." % (new_stack['name'], environment_name))
                r = session.post("%s/projects/%s/environments" % (
                    api,
                    environment_id
                ), json=new_stack)
                r.raise_for_status()
                rancher_stack_name = r.json()
            except requests.exceptions.HTTPError:
                bail("Unable to create missing stack")
        else:
            bail("Unable to find a stack called '%s'. Does it exist in the '%s' environment?" % (
                rancher_stack_name, environment_name))

    # 3 -> Find the service in the stack

    try:
        r = session.get("%s/projects/%s/environments/%s/services?limit=1000" % (
            api,
            environment_id,
            rancher_stack_name['id']
        ))
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        bail("Unable to fetch a list of services in the stack. Does your API key have the right permissions?")
    else:
        services = r.json()['data']

    # Loop through all services and find the one that matches the command line argument
    for s in services:
        if s['name'].lower() == rancher_service_name.lower():
            rancher_service_name = s
            break
    else:
        # We didn't find the specified service, so if the 'create' flag is set, let's try to create a new service
        if create:
            new_service = {
                'name': rancher_service_name.lower(),
                'stackId': rancher_stack_name['id'],
                'startOnCreate': True,
                'launchConfig': {
                    'imageUuid': ("docker:%s" % new_image),
                    'labels': defined_labels,
                    'environment': defined_environment_variables
                }
            }
            try:
                msg("Creating service %s in environment %s with image %s..." % (
                    new_service['name'], environment_name, new_image
                ))
                r = session.post("%s/projects/%s/services" % (
                    api,
                    environment_id
                ), json=new_service)
                r.raise_for_status()
                rancher_service_name = r.json()

                msg("Creation finished")
                # sys.exit(0)
            except requests.exceptions.HTTPError:
                bail("Unable to create missing service")
        else:
            bail("Unable to find a service called '%s', does it exist in Rancher?" % rancher_service_name)

    # 4 -> Is the service elligible for upgrade?

    if rancher_service_name['state'] == 'upgraded':
        warn(
            "The current service state is 'upgraded', marking the previous upgrade as finished before starting a new upgrade...")

        try:
            r = session.post("%s/projects/%s/services/%s/?action=finishupgrade" % (
                api, environment_id, rancher_service_name['id']
            ))
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            bail("Unable to finish the previous upgrade in Rancher")

        attempts = 0
        while rancher_service_name['state'] != "active":
            sleep(2)
            attempts += 2
            if attempts > upgrade_timeout:
                bail("A timeout occured while waiting for Rancher to finish the previous upgrade")
            try:
                r = session.get("%s/projects/%s/services/%s" % (
                    api, environment_id, rancher_service_name['id']
                ))
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                bail("Unable to request the service status from the Rancher API")
            else:
                rancher_service_name = r.json()

    # if service['state'] != 'active':
    #     bail("Unable to start upgrade: current service state '%s', but it needs to be 'active'" % service['state'])

    msg("Upgrading %s/%s in environment %s..." % (rancher_stack_name['name'], rancher_service_name['name'], environment_name))

    upgrade = {'inServiceStrategy': {
        'batchSize': batch_size,
        'intervalMillis': batch_interval * 1000,  # rancher expects miliseconds
        'startFirst': start_before_stopping,
        'launchConfig': {
        },
        'secondaryLaunchConfigs': []
    }}
    # copy over the existing config
    upgrade['inServiceStrategy']['launchConfig'] = rancher_service_name['launchConfig']

    if defined_labels:
        upgrade['inServiceStrategy']['launchConfig']['labels'].update(defined_labels)

    if defined_environment_variables:
        upgrade['inServiceStrategy']['launchConfig']['environment'].update(defined_environment_variables)

    # new_sidekick_image parameter needs secondaryLaunchConfigs loaded
    if sidekicks or new_sidekick_image:
        # copy over existing sidekicks config
        upgrade['inServiceStrategy']['secondaryLaunchConfigs'] = rancher_service_name['secondaryLaunchConfigs']

    if new_image:
        # place new image into config
        upgrade['inServiceStrategy']['launchConfig']['imageUuid'] = 'docker:%s' % new_image

    if new_sidekick_image:
        new_sidekick_image = dict(new_sidekick_image)

        for idx, secondaryLaunchConfigs in enumerate(rancher_service_name['secondaryLaunchConfigs']):
            if secondaryLaunchConfigs['name'] in new_sidekick_image:
                upgrade['inServiceStrategy']['secondaryLaunchConfigs'][idx]['imageUuid'] = 'docker:%s' % \
                                                                                           new_sidekick_image[
                                                                                               secondaryLaunchConfigs[
                                                                                                   'name']]

    # 5 -> Start the upgrade
    ##### NEW FUNCTION HERE <-----------------------
    try:
        r = session.post("%s/projects/%s/services/%s/?action=upgrade" % (
            api, environment_id, rancher_service_name['id']
        ), json=upgrade)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        bail("Unable to request an upgrade on Rancher")

    # 6 -> Wait for the upgrade to finish

    if not wait_for_upgrade_to_finish and not defined_service_links:
        msg("Upgrade started")
    else:
        msg("Upgrade started, waiting for upgrade to complete...")
        attempts = 0
        while rancher_service_name['state'] != "upgraded":
            sleep(2)
            attempts += 2
            if attempts > upgrade_timeout:
                message = "A timeout occured while waiting for Rancher to complete the upgrade"
                if rollback_on_error:
                    bail(message, exit=False)
                    warn("Processing image rollback...")

                    try:
                        r = session.post("%s/projects/%s/services/%s/?action=rollback" % (
                            api, environment_id, rancher_service_name['id']
                        ))
                        r.raise_for_status()
                    except requests.exceptions.HTTPError:
                        bail("Unable to request a rollback on Rancher")

                    attempts = 0
                    while rancher_service_name['state'] != "active":
                        sleep(2)
                        attempts += 2
                        if attempts > upgrade_timeout:
                            bail(
                                "A timeout occured while waiting for Rancher to rollback the upgrade to its latest running state")
                        try:
                            r = session.get("%s/projects/%s/services/%s" % (
                                api, environment_id, rancher_service_name['id']
                            ))
                            r.raise_for_status()
                        except requests.exceptions.HTTPError:
                            bail("Unable to request the service status from the Rancher API")
                        else:
                            rancher_service_name = r.json()

                    warn("Service sucessfully rolled back")
                    sys.exit(1)
                else:
                    bail(message)
            try:
                r = session.get("%s/projects/%s/services/%s" % (
                    api, environment_id, rancher_service_name['id']
                ))
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                bail("Unable to fetch the service status from the Rancher API")
            else:
                rancher_service_name = r.json()

        if not finish_upgrade and not defined_service_links:
            msg("Service upgraded")
            sys.exit(0)
        else:
            msg("Finishing upgrade...")
            try:
                r = session.post("%s/projects/%s/services/%s/?action=finishupgrade" % (
                    api, environment_id, rancher_service_name['id']
                ))
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                bail("Unable to finish the upgrade in Rancher")

            attempts = 0
            while rancher_service_name['state'] != "active":
                sleep(2)
                attempts += 2
                if attempts > upgrade_timeout:
                    bail("A timeout occured while waiting for Rancher to finish the previous upgrade")
                try:
                    r = session.get("%s/projects/%s/services/%s" % (
                        api, environment_id, rancher_service_name['id']
                    ))
                    r.raise_for_status()
                except requests.exceptions.HTTPError:
                    bail("Unable to request the service status from the Rancher API")
                else:
                    rancher_service_name = r.json()

            msg("Upgrade finished")

            if defined_service_links:
                set_service_links(defined_service_links)

    sys.exit(0)


# ======================================================================================================================
# A function to set service links on a service
# ======================================================================================================================
def set_service_links(new_service_links, session, api, environment_id, service, timeout):
    msg("Setting service links for service %s in environment %s with image %s..." % (
        service['name'], environment_name, new_image
    ))
    # Kill service for now
    r = session.post("%s/projects/%s/services/%s/?action=deactivate" % (
        api, environment_id, service['id']
    ))
    service = r.json()
    attempts = 0
    while service['state'] != "inactive":
        sleep(2)
        attempts += 2
        if attempts > upgrade_timeout:
            bail("A timeout occured while waiting for the service to shut down.")
        try:
            r = session.get("%s/projects/%s/services/%s" % (
                api, environment_id, service['id']
            ))
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            bail("Unable to request the service status from the Rancher API")
        else:
            service = r.json()

    # service should be down. Let's add the service links
    r = session.post(service['actions']['setservicelinks'], json={'serviceLinks': defined_service_links})
    r.raise_for_status()
    service = r.json()

    # now bring the service back up
    r = session.post("%s/projects/%s/services/%s/?action=active" % (
        api, environment_id, service['id']
    ))
    service = r.json()
    attempts = 0
    while service['state'] != "active":
        sleep(2)
        attempts += 2
        if attempts > upgrade_timeout:
            bail("A timeout occured while waiting for the service to start.")
        try:
            r = session.get("%s/projects/%s/services/%s" % (
                api, environment_id, service['id']
            ))
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            bail("Unable to request the service status from the Rancher API")
        else:
            service = r.json()
    msg("Service links set")


# ======================================================================================================================
# A function to retrieve and return a service ID based on a service reference in the service link argument
# ======================================================================================================================
def get_service_id_from_link_reference(service_link_reference, session, api, environment_id, environment_name):
    # service references are in the form of '<stack>/<service>'
    stack_name, service_name = service_link_reference.split('/')
    return get_service_id(stack_name, service_name, session, api, environment_id, environment_name)


# ======================================================================================================================
# A function to retrieve and return a service ID based on a service reference in the service link argument
# ======================================================================================================================
def get_service_id(stack_name, service_name, session, api, environment_id, environment_name):
    service_id = None
    services = None
    stack_id = get_stack_id(stack_name, session, api, environment_id, environment_name)

    if stack_id:
        try:
            r = session.get("%s/projects/%s/environments/%s/services?limit=1000" % (
                api,
                environment_id,
                stack_id
            ))
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            bail("Unable to fetch a list of services in stack '%s'. Does your API key have the right permissions?"
                 % stack_name, False)
            return service_id
        else:
            services = r.json()['data']

        # Loop through all services and find the one that matches the command line argument
        for s in services:
            if s['name'].lower() == service_name:
                service_id = s['id']
                break

    return service_id


# ======================================================================================================================
# A function to retrieve and return a stack ID based on a stack name
# ======================================================================================================================
def get_stack_id(stack_name, session, api, environment_id, environment_name):
    stack_id = None
    stacks = None

    try:
        r = session.get("%s/projects/%s/environments?limit=1000" % (
            api,
            environment_id
        ))
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        bail("Unable to fetch a list of stacks in the environment '%s'" % environment_name, False)
        return stack_id
    else:
        stacks = r.json()['data']

    for stack in stacks:
        if stack['name'] == stack_name.lower():
            stack_id = stack['id']
            break

    return stack_id


# ======================================================================================================================
# A function to
# ======================================================================================================================
def msg(message):
    click.echo(click.style(message, fg='green'))


# ======================================================================================================================
# A function to
# ======================================================================================================================
def warn(message):
    click.echo(click.style(message, fg='yellow'))


# ======================================================================================================================
# A function to
# ======================================================================================================================
def bail(message, exit=True):
    click.echo(click.style('Error: ' + message, fg='red'))
    if exit:
        sys.exit(1)


# ======================================================================================================================
# A function to turn on debug logging
# ======================================================================================================================
def debug_requests_on():
    """Switches on logging of the requests module."""
    HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

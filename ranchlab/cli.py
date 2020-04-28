#!/usr/bin/env python
import logging
import click
import sys

from lib import Logger, LogLevel
from lib import RancherConnection

try:
    from http.client import HTTPConnection  # py3
except ImportError:
    from httplib import HTTPConnection  # py2


@click.command()
@click.option('--rancher-url', envvar='RANCHER_URL', required=True,
              help='The URL for your Rancher server.')
@click.option('--rancher-key', envvar='RANCHER_ACCESS_KEY', required=True,
              help="The environment or account API Access Key.")
@click.option('--rancher-secret', envvar='RANCHER_SECRET_KEY', required=True,
              help="The secret for the API Access Key.")
@click.option('--stack', 'rancher_stack_name', envvar='CI_PROJECT_NAMESPACE', default=None, required=True,
              help="The name of the target stack in Rancher. Defaults to the name of the GitLab project group as "
                   "defined in the CI_PROJECT_NAMESPACE environment variable.")
@click.option('--service', 'rancher_service_name', envvar='CI_PROJECT_NAME', default=None, required=True,
              help="The name of the service in Rancher to upgrade/create. Defaults to the name of the GitLab project "
                   "as defined in the CI_PROJECT_NAME environment variable.")
@click.option('--api-version', 'rancher_api_version', default='v2-beta', required=False,
              type=click.Choice(['v1', 'v2-beta'], case_sensitive=True),
              help="The API version to use. Rancher versions < 2 have API versions v1 and v2-beta. The default is "
                   "v2-beta.")
@click.option('--environment', 'rancher_project_name', default=None,
              help="The name of the Rancher environment to operate in. In the Rancher API, this is called 'project'." +
                   "This is only required if you are using an account API key instead of an environment API key.")
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
@click.option('--log-level', envvar='LOG_LEVEL',
              type=click.Choice(['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL', 'SILENT'], case_sensitive=False),
              help="Determines how much information is written to the console. RanchLab will first check to see if "
                   "this argument is provided. If not, it will check for a 'LOG_LEVEL' environment variable. If the "
                   "'LOG_LEVEL' environment variable isn't set, it will default to INFO.")
@click.option('--debug-http/--no-debug-http', default=False,
              help="Sets whether or not to enable debug mode for HTTP requests. Defaults to --no-debug-http.")
@click.option('--ssl-verify/--no-ssl-verify', default=True,
              help="Sets whether or not to perform certificate checks. Defaults to --ssl-verify. Use this to allow "
                   "connecting to a HTTPS Rancher server using an self-signed certificate")
def main(rancher_url, rancher_key, rancher_secret, rancher_api_version, rancher_project_name, rancher_stack_name,
         rancher_service_name, new_service_image, batch_size, batch_interval,
         start_before_stopping, timeout, wait_for_finish, rollback_on_error, finish_on_success,
         sidekicks, new_sidekick_image, create_stack, create_service, labels, label, variables, variable,
         service_links, service_link, log_level, debug_http, ssl_verify):
    """
    Performs an in service upgrade of the service specified on the command line
    """

    log = Logger(log_level, 'Main')
    log.trace('Log level set to ' + log.level.name)

    if log.level >= LogLevel.DEBUG:
        log.trace('Turning on debug mode for HTTP requests')

    if debug_http:
        debug_requests_on()

    # split url to protocol and host
    if "://" not in rancher_url:
        log.fatal("The Rancher URL doesn't look right. Please verify that it's a valid URL (i.e. "
                  "https://my.rancher.com).")

    proto, host = rancher_url.split("://")

    rancher = RancherConnection(
        "%s://%s/" % (proto, host),
        rancher_key,
        rancher_secret,
        rancher_project_name,
        rancher_stack_name,
        rancher_service_name,
        ssl_verify,
        rancher_api_version,
        log.level,
        timeout
    )

    # Check for labels and environment variables to set
    rancher.add_labels(labels)
    rancher.add_labels(label)
    rancher.add_variables(variables)
    rancher.add_variables(variable)
    rancher.add_service_links(service_links)
    rancher.add_service_links(service_link)

    # 1 -> Find the environment id in Rancher (aka "project")

    # While we're here, let's define service links if provided

    # 2 -> Find the stack (aka "environment") in the environment (aka "project")
    if not rancher.stack_exists():
        if create_stack:
            if rancher.create_stack():
                log.trace('Successfully created stack')
            else:
                log.fatal("Creating stack failed.")
        else:
            log.fatal("Unable to find a stack called '%s'. Does it exist in the '%s' environment?" % (
                rancher_stack_name, rancher_project_name))

    # 3 -> Find the service in the stack

    if not rancher.service_exists():
        # We didn't find the specified service, so if the 'create' flag is set, let's try to create a new service
        if create_service:
            rancher.create_service(new_service_image)
        else:
            log.fatal("Unable to find a service called '%s', does it exist in Rancher?" % rancher_service_name)

    # 4 -> Is the service elligible for upgrade?

    if rancher.get_service_state() == 'upgraded':
        log.warn(
            "The current service state is 'upgraded', marking the previous upgrade as finished before starting a new "
            "upgrade...")
        rancher.finish_upgrade()

    log.info("Upgrading %s/%s in environment %s..." % (rancher_stack_name, rancher_service_name, rancher_project_name))

    upgrade = {'inServiceStrategy': {
        'batchSize': batch_size,
        'intervalMillis': batch_interval * 1000,  # rancher expects miliseconds
        'startFirst': start_before_stopping,
        'launchConfig': {
        },
        'secondaryLaunchConfigs': []
    }}
    # copy over the existing config
    upgrade['inServiceStrategy']['launchConfig'] = rancher.get_launch_config()

    if rancher.get_labels():
        upgrade['inServiceStrategy']['launchConfig']['labels'].update(rancher.get_labels())

    if rancher.get_variables():
        upgrade['inServiceStrategy']['launchConfig']['environment'].update(rancher.get_variables())

    # new_sidekick_image parameter needs secondaryLaunchConfigs loaded
    if sidekicks or new_sidekick_image:
        # copy over existing sidekicks config
        upgrade['inServiceStrategy']['secondaryLaunchConfigs'] = rancher.get_launch_config(True)

    if new_service_image:
        # place new image into config
        upgrade['inServiceStrategy']['launchConfig']['imageUuid'] = 'docker:%s' % new_service_image

    if new_sidekick_image:
        new_sidekick_image = dict(new_sidekick_image)

        for idx, secondaryLaunchConfigs in enumerate(upgrade['secondaryLaunchConfigs']):
            if secondaryLaunchConfigs['name'] in new_sidekick_image:
                upgrade['inServiceStrategy']['secondaryLaunchConfigs'][idx]['imageUuid'] = 'docker:%s' % \
                                                                                           new_sidekick_image[
                                                                                               secondaryLaunchConfigs[
                                                                                                   'name']]

    # 5 -> Start the upgrade
    rancher.do_upgrade(upgrade)

    # 6 -> Wait for the upgrade to finish

    if not wait_for_finish and not rancher.get_service_links():
        log.info("Upgrade triggered. Not waiting for finish.")
    else:
        log.info("Upgrade started, waiting for upgrade to complete...")
        if not rancher.wait_for_state('upgraded'):
            if rollback_on_error:
                log.info("Processing image rollback...")
                if not rancher.rollback():
                    log.fatal("Rollback failed.")
                log.info("Rollback request submitted. Waiting for container to come back online.")
                attempts = 0
                if not rancher.wait_for_state('active'):
                    log.fatal("A timeout occurred while waiting for Rancher to rollback the upgrade to its "
                              "latest running state. Please check Rancher and resolve the problem.")

                log.fatal("Service successfully rolled back. Please investigate why the upgrade failed and resolve "
                          "any issued before trying again.")
            else:
                log.fatal("The upgrade failed. Please investigate the cause and resolve "
                          "any issues before trying again.")

        if not finish_on_success and not rancher.get_service_links():
            log.info("Service upgraded. Upgrade still needs to be manually finished.")
        else:
            log.info("Finishing upgrade...")
            rancher.finish_upgrade()

            if not rancher.wait_for_state('active'):
                log.fatal("Something happened while waiting for the upgraded to be finished. Please investigate the "
                          "cause and resolve any issues before trying again.")

            log.info("Upgrade finished.")

            # if rancher.get_service_links():
            #     set_service_links(defined_service_links)

    log.info("Processing complete. Exiting.")
    sys.exit(0)


# # ======================================================================================================================
# # A function to set service links on a service
# # ======================================================================================================================
# def set_service_links(new_service_links, session, api, environment_id, service, timeout):
#     msg("Setting service links for service %s in environment %s with image %s..." % (
#         service['name'], environment_name, new_image
#     ))
#     # Kill service for now
#     r = session.post("%s/projects/%s/services/%s/?action=deactivate" % (
#         api, environment_id, service['id']
#     ))
#     service = r.json()
#     attempts = 0
#     while service['state'] != "inactive":
#         sleep(2)
#         attempts += 2
#         if attempts > upgrade_timeout:
#             bail("A timeout occured while waiting for the service to shut down.")
#         try:
#             r = session.get("%s/projects/%s/services/%s" % (
#                 api, environment_id, service['id']
#             ))
#             r.raise_for_status()
#         except requests.exceptions.HTTPError:
#             bail("Unable to request the service status from the Rancher API")
#         else:
#             service = r.json()
#
#     # service should be down. Let's add the service links
#     r = session.post(service['actions']['setservicelinks'], json={'serviceLinks': defined_service_links})
#     r.raise_for_status()
#     service = r.json()
#
#     # now bring the service back up
#     r = session.post("%s/projects/%s/services/%s/?action=active" % (
#         api, environment_id, service['id']
#     ))
#     service = r.json()
#     attempts = 0
#     while service['state'] != "active":
#         sleep(2)
#         attempts += 2
#         if attempts > upgrade_timeout:
#             bail("A timeout occured while waiting for the service to start.")
#         try:
#             r = session.get("%s/projects/%s/services/%s" % (
#                 api, environment_id, service['id']
#             ))
#             r.raise_for_status()
#         except requests.exceptions.HTTPError:
#             bail("Unable to request the service status from the Rancher API")
#         else:
#             service = r.json()
#     msg("Service links set")

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

#!/usr/bin/env python

import logging
import click
import sys

from .helpers import RancherConnection
from .helpers import Logger

try:
    from http.client import HTTPConnection  # py3
except ImportError:
    from httplib import HTTPConnection  # py2

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group()
@click.pass_context
# <editor-fold desc="click options">
@click.option('--log-level', envvar='LOG_LEVEL', default="INFO",
              type=click.Choice(['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL', 'SILENT'], case_sensitive=False),
              help="Determines how much information is written to the console. Ranchertool will first check to see if "
                   "this argument is provided. If not, it will check for a 'LOG_LEVEL' environment variable. If the "
                   "'LOG_LEVEL' environment variable isn't set, it will use the default. DEFAULT: INFO")
@click.option('--debug-http/--no-debug-http', default=False,
              help="Sets whether or not to enable debug mode for HTTP requests. DEFAULT: --no-debug-http")
@click.option('--rancher-url', envvar='RANCHER_URL', required=True,
              help='The URL for your Rancher server.')
@click.option('--rancher-key', envvar='RANCHER_ACCESS_KEY', required=True,
              help="The environment or account API Access Key.")
@click.option('--rancher-secret', envvar='RANCHER_SECRET_KEY', required=True,
              help="The secret for the API Access Key.")
@click.option('--stack', 'rancher_stack_name', envvar='RANCHER_STACK', default=None, required=True,
              help="The name of the target stack in Rancher. Defaults to the name of the GitLab project group as "
                   "defined in the CI_PROJECT_NAMESPACE environment variable.")
@click.option('--service', 'rancher_service_name', envvar='RANCHER_SERVICE', default=None, required=True,
              help="The name of the service in Rancher to upgrade/create. Defaults to the name of the GitLab project "
                   "as defined in the CI_PROJECT_NAME environment variable.")
@click.option('--api-version', 'rancher_api_version', default='v2-beta', required=False,
              type=click.Choice(['v1', 'v2-beta'], case_sensitive=True),
              help="The API version to use. Rancher versions < 2 have API versions v1 and v2-beta. The default is "
                   "v2-beta.")
@click.option('--environment', 'rancher_project_name', default=None,
              help="The name of the Rancher environment to operate in. In the Rancher API, this is called 'project'." +
                   "This is only required if you are using an account API key instead of an environment API key.")
@click.option('--timeout', default=5 * 60,
              help="Sets how many seconds to wait for Rancher to finish processing before assuming something went "
                   "wrong. Defaults to 300 seconds (5 mins). This setting is ignored if --no-wait is used.")
@click.option('--ssl-verify/--no-ssl-verify', default=True,
              help="Sets whether or not to perform certificate checks. Defaults to --ssl-verify. Use this to allow "
                   "connecting to a HTTPS Rancher server using an self-signed certificate")
# </editor-fold>
def cli(ctx, log_level, debug_http, rancher_url, rancher_key, rancher_secret, rancher_stack_name, rancher_service_name,
        rancher_api_version, rancher_project_name, timeout, ssl_verify):
    ctx.ensure_object(dict)
    logger = Logger(log_level, 'MAIN')
    if debug_http:
        logger.debug('Enabling HTTP debug mode')
        debug_requests_on()
    logger.debug('Logging level set to %s' % log_level)

    # split url to protocol and host
    if "://" not in rancher_url:
        logger.fatal("The Rancher URL doesn't look right. Please verify that it's a valid URL (i.e. "
                     "https://my.rancher.com).")
    logger.trace("Rancher URL: %s" % rancher_url)

    proto, host = rancher_url.split("://")

    rancher = RancherConnection(
        "%s://%s" % (proto, host),
        rancher_key,
        rancher_secret,
        rancher_project_name,
        rancher_stack_name,
        rancher_service_name,
        ssl_verify,
        rancher_api_version,
        logger.level,
        timeout
    )
    logger.info("Setting LOG_LEVEL in context...")
    ctx.obj['LOG_LEVEL'] = log_level
    logger.info("Setting RANCHER_CONNECTION in context...")
    ctx.obj['RANCHER_CONNECTION'] = rancher


@cli.command(name="delete")
@click.pass_context
def _delete(ctx):
    """
    Deletes the specified service.

    \f
    :param ctx:
    :return:
    """
    log = Logger(ctx.obj['LOG_LEVEL'], 'DELETE')
    log.info("Deleting service...")
    rancher = ctx.obj['RANCHER_CONNECTION']
    if rancher.service_exists():
        log.debug("Removing service %s" % rancher.get_service_name())
        rancher.remove_service()
    else:
        log.info("Unable to remove service %s. Are you sure it exists?" % rancher.get_service_name())


@cli.command(name="stop")
@click.pass_context
def _stop(ctx):
    """
    Stops the specified service.

    \f
    :param ctx:
    :return:
    """
    log = Logger(ctx.obj['LOG_LEVEL'], 'STOP')
    log.info("Stopping service...")
    rancher = ctx.obj['RANCHER_CONNECTION']
    if rancher.service_exists() and rancher.get_service_state() == 'active':
        log.debug("Stopping service %s" % rancher.get_service_name())
        rancher.deactivate_service()
    else:
        log.info("Unable to stop service %s. This is due to either the service wasn't found or it isn't "
                 "currently active." % rancher.get_service_name())


@cli.command()
@click.pass_context
def restart(ctx):
    """
    Deletes the specified service.

    \f
    :param ctx:
    :return:
    """
    logger = ctx.obj['LOGGER']
    rancher = ctx.obj['RANCHER_CONNECTION']
    logger.info("Restarting")


@cli.command(name='deploy')
@click.pass_context
# <editor-fold desc="click options">
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
@click.option('--upgrade-sidekicks/--no-upgrade-sidekicks', default=False,
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
                   "pipe-delimited list of <label-name>=<label-value> pairs.")
@click.option('--secrets', default=None,
              help="If specified, environment secrets will be added to the service. Secrets to be added should be "
                   "provided as a "
                   "pipe-delimited list of <environment-secret>=<container-secret> pairs.")
@click.option('--variables', default=None,
              help="If specified, adds the passed list of environment variables to the service. The list of variables "
                   "should be a pipe-delimited (|) list of <key>=<value> pairs. "
                   "Example: '--variables var1=val1|var2=val2|var3=val3'.")
@click.option('--service-links', default=None,
              help="If specified, adds the provided list of service links to the service. See --labels for syntax. "
                   "Example: '--service-links <local-name1>=<target-name1>|<local-name2>=<target-name2>'. Target "
                   "service name should be in the format of '<stack>/<service>'.")
# </editor-fold>
def _deploy(ctx,
            start_before_stopping,
            batch_size,
            batch_interval,
            timeout,
            wait_for_finish,
            rollback_on_error,
            new_service_image,
            finish_on_success,
            upgrade_sidekicks,
            new_sidekick_image,
            create_stack,
            create_service,
            labels,
            secrets,
            variables,
            service_links
            ):
    log = Logger(ctx.obj['LOG_LEVEL'], 'DEPLOY')
    log.info("Deploying image...")
    rancher = ctx.obj['RANCHER_CONNECTION']

    # Check for labels and environment variables to set
    rancher.set_labels(labels)
    rancher.set_variables(variables)
    rancher.set_service_links(service_links)
    rancher.set_secrets(secrets)

    # 1 -> Find the environment id in Rancher (aka "project")

    # While we're here, let's define service links if provided

    # 2 -> Find the stack (aka "environment") in the environment (aka "project")
    if not rancher.stack_exists():
        if create_stack:
            if rancher.create_stack():
                log.info('Successfully created stack')
            else:
                log.fatal("Creating stack failed.")
        else:
            log.fatal("Unable to find a stack called '%s'. Does it exist in the '%s' environment?" % (
                rancher.get_stack_name(), rancher.get_project_name()))

    # 3 -> Find the service in the stack
    if not rancher.service_exists():
        # We didn't find the specified service, so if the 'create' flag is set, let's try to create a new service
        if create_service:
            if not rancher.create_service(new_service_image):
                log.fatal("Failed to create a service called '%s'." % rancher.get_service_name())
            log.info("Service was successfully created. Thank you and have a nice day!")
            exit(0)
        else:
            log.fatal("Unable to find a service called '%s', does it exist in Rancher?" % rancher.get_service_name())

    # 4 -> Is the service eligible for upgrade?
    if rancher.get_service_state() == 'upgraded':
        log.warn(
            "The current service state is 'upgraded'. Finishing the previous upgrade before starting a new "
            "one...")
        rancher.finish_upgrade()

    log.info("Upgrading %s/%s in environment %s..."
             % (rancher.get_stack_name(), rancher.get_service_name(), rancher.get_project_name()))

    upgrade = {'inServiceStrategy': {
        'batchSize': batch_size,
        'intervalMillis': batch_interval * 1000,  # rancher expects milliseconds
        'startFirst': start_before_stopping,
        'launchConfig': {
        },
        'secondaryLaunchConfigs': []
    }}

    # copy over the current launchConfig
    upgrade['inServiceStrategy']['launchConfig'] = rancher.get_launch_config()

    if rancher.get_labels():
        upgrade['inServiceStrategy']['launchConfig']['labels'] = (rancher.get_labels())

    if rancher.get_variables():
        upgrade['inServiceStrategy']['launchConfig']['environment'] = (rancher.get_variables())

    if rancher.get_secrets():
        upgrade['inServiceStrategy']['launchConfig']['secrets'] = (rancher.get_secrets())

    # new_sidekick_image parameter needs secondaryLaunchConfigs loaded
    if upgrade_sidekicks or new_sidekick_image:
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

    if not wait_for_finish:
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

        if not finish_on_success:
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

    log.info("Processing complete. Have a nice day!")
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


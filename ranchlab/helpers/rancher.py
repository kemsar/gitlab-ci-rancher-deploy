import requests
from time import sleep

from .logger import Logger, LogLevel
from enum import Enum, auto
from sakstig import *
import json


class UrlFragType(Enum):
    PROJECT_BASE = auto()
    PROJECT = auto()
    STACK_BASE = auto()
    STACK = auto()
    SERVICE_BASE = auto()
    SERVICE = auto()


class HttpMethod(Enum):
    GET = auto()
    POST = auto()


class RancherConnection:
    """
    A class to package current info regarding the Rancher instance we're working with.
    """

    def __init__(self, url, api_key, api_secret, project_name, stack_name, service_name,
                 verify_ssl=True, api_version='v2-beta', log_level=LogLevel.INFO, operation_timeout=300):
        """
        Default constructor
        """
        self.__logger = Logger(log_level, 'RancherConnection')
        self.__logger.trace('Instantiating instance of RancherConnection....')
        self.__url = url
        self.__api_version = api_version
        self.__stack_name = stack_name
        self.__stack_id = None
        self.__service_name = service_name
        self.__service_id = None
        self.__project_name = project_name
        self.__session = requests.Session()
        self.__session.verify = verify_ssl
        self.__session.auth = (api_key, api_secret)
        self.__labels = {}
        self.__variables = {}
        self.__service_links = {'serviceLinks': []}
        self.__api_endpoint = self.__url + '/' + self.__api_version
        self.__project_id = self.__get_project_id()
        self.__key = None
        self.__secret = None
        self.__timeout = operation_timeout

    def get_project_name(self):
        return self.__project_name

    def get_stack_name(self):
        return self.__stack_name

    def get_service_name(self):
        return self.__service_name

    def set_labels(self, labels_in):
        """
        Process the labels arguments
        :param labels_in: A string of comma-delimited key=value pairs
        :return:
        """
        try:
            self.__logger.trace('Adding labels...')
            if labels_in is not None and isinstance(labels_in, str):
                self.__logger.trace('Adding a string of labels')
                self.__logger.trace(labels_in)
                label_array = labels_in.split(',')
                for label_pair in label_array:
                    label, value = label_pair.split('=', 1)
                    self.__logger.trace("Adding label '" + label + "' with value '" + value + "'.")
                    self.__labels[label] = value
            elif labels_in and (isinstance(labels_in, tuple) or isinstance(labels_in, list)):
                self.__logger.trace('adding labels from a tuple or list')
                for label in labels_in:
                    name, value = label
                    self.__logger.trace("Adding label '" + name + "' with value '" + value + "'.")
                    self.__labels[name] = value
            else:
                self.__logger.error('Unknown type of labels provided. Ignoring them.')
        except Exception as e:
            self.__logger.error("%s" % format(e))

    def get_labels(self):
        return self.__labels

    def set_variables(self, vars_in):
        try:
            if vars_in is not None and isinstance(vars_in, str):
                self.__logger.debug("Processing a string of variables")
                self.__logger.trace(vars_in)
                variables_as_array = vars_in.split('|')
                for variable_item in variables_as_array:
                    key, value = variable_item.split('=', 1)
                    self.__variables[key] = value
            elif vars_in and (isinstance(vars_in, tuple) or isinstance(vars_in, list)):
                self.__logger.debug("Processing a tuple or list of variables")
                for variable in vars_in:
                    name, value = variable
                    self.__logger.trace("Adding variable '" + name + "' with value '" + value + "'.")
                    self.__variables[name] = value
            else:
                self.__logger.error('Unknown type of variables provided. Ignoring them.')
        except Exception as e:
            self.__logger.error("%s" % format(e))

    def get_variables(self):
        return self.__variables

    def set_service_links(self, links_in):
        self.__logger.trace("Adding service links")
        if links_in and links_in is not None and isinstance(links_in, str):
            self.__logger.trace("Processing a string of service links")
            link_array = links_in.split(',')
            if len(link_array) > 0:
                for link in link_array:
                    try:
                        name, reference = link.split('=', 1)
                        self.__logger.trace("Adding link named '" + name + "' linking to service '" + reference + "'.")
                        service_id = self.__get_service_id_from_link_reference(reference)
                        if service_id is not None and name is not None:
                            self.__service_links['serviceLinks'].append({'name': name, 'serviceId': service_id})
                    except Exception as e:
                        self.__logger.error("%s" % format(e))
        elif links_in and (isinstance(links_in, tuple) or isinstance(links_in, list)):
            self.__logger.trace("Processing a tuple or list of services links")
            for link in links_in:
                try:
                    name, reference = link
                    self.__logger.trace("Adding link named '" + name + "' linking to service '" + reference + "'.")
                    service_id = self.__get_service_id_from_link_reference(reference)
                    if service_id is not None:
                        self.__service_links['serviceLinks'].append({'name': name, 'serviceId': service_id})
                except Exception as e:
                    self.__logger.error("%s" % format(e))
        else:
            self.__logger.error("Unrecognized type of service links. Ignoring them and moving on.")

    def get_service_links(self):
        return self.__service_links

    def stack_exists(self, stack_name=None):
        return self.__get_stack_id(str(stack_name or self.__stack_name)) is not None

    def create_stack(self, stack_name=None):
        if stack_name is None:
            stack_name = self.__stack_name
        if self.stack_exists(stack_name):
            self.__logger.error("Stack '%s' already exists. Skipping create action." % stack_name)
            return False
        new_stack = {
            'name': stack_name
        }
        self.__logger.info("Creating stack %s in environment %s..." % (new_stack['name'], self.__project_name))
        response = self.__managed_session(
            HttpMethod.POST,
            self.__get_url_frag(UrlFragType.STACK_BASE),
            "Failed to create stack named '%s'." % stack_name,
            '$.*[@.name is "%s"].id' % stack_name,
            new_stack
        )
        if response is not None:
            self.__stack_id = response
            return True
        else:
            return False

    def service_exists(self, service_name=None):
        if service_name is None:
            service_name = self.__service_name
        if self.__stack_id is None:
            self.__stack_id = self.__get_stack_id()
        response = self.__managed_session(
            HttpMethod.GET,
            self.__get_url_frag(UrlFragType.SERVICE_BASE),
            "Failed to determine if service '%s' exists",
            '$.data[@.name is "%s"]' % str(service_name or self.__service_name))
        if response is not None:
            return True
        else:
            return False

    def create_service(self, new_image, service_name=None):
        if service_name is None:
            service_name = self.__service_name
        if new_image is None:
            self.__logger.error("In order to create service %s, an image must be specified." % service_name)
            return False
        if self.service_exists(service_name):
            self.__logger.error("Service '%s' already exists. Skipping create." % service_name)
            return False
        new_service = {
            'name': service_name,
            'stackId': self.__stack_id,
            'startOnCreate': False,
            'launchConfig': {
                'imageUuid': ("docker:%s" % new_image),
                'labels': self.__labels,
                'environment': self.__variables
            }
        }
        self.__logger.info("Creating service %s in stack %s in environment %s..." %
                           (new_service['name'], self.__stack_name, self.__project_name))
        response = self.__managed_session(
            HttpMethod.POST,
            self.__get_url_frag(UrlFragType.SERVICE_BASE),
            "Failed to create service named '%s'." % service_name,
            '$.*[@.name is "%s"].id' % service_name,
            new_service
        )
        if response is not None:
            self.__service_id = response
            self.__set_service_links()
            return self.activate_service() and self.wait_for_state('active')
        else:
            return False

    def get_service_state(self, service_id=None):
        service_id = self.__get_actionable_service_id(service_id)
        response = self.__managed_session(
            HttpMethod.GET,
            self.__get_url_frag(UrlFragType.SERVICE_BASE),
            "Failed to determine if service '%s' exists.",
            '$.data[@.id is "%s"].state' % service_id)
        if response is not None:
            return response
        else:
            return None

    def wait_for_state(self, state, service_id=None):
        service_id = self.__get_actionable_service_id(service_id)
        elapsed = 0
        while self.get_service_state(service_id) != state:
            self.__logger.trace("Waiting for state to be %s...." % state)
            sleep(2)
            elapsed += 2
            if elapsed >= self.__timeout:
                self.__logger.error("Waiting for container timed out")
                return False
        return True

    def finish_upgrade(self, service_id=None):
        service_id = self.__get_actionable_service_id(service_id)
        if self.get_service_state(service_id) == 'active':
            self.__logger.warn("Service with id %s is currently Active. No upgrade to finish." % service_id)
        else:
            if self.wait_for_state('upgraded'):
                response = self.__managed_session(
                    HttpMethod.POST,
                    self.__get_url_frag(UrlFragType.SERVICE, None, service_id) + '/?action=finishupgrade',
                    "Error while finishing upgrade of service id '%s'." % service_id,
                    '$.*[@.id is "%s"]' % service_id
                )
                return self.wait_for_state('active')
            else:
                return False

    def get_launch_config(self, secondary=False, service_id=None):
        self.__logger.trace('Executing get_launch_config....')
        service_id = self.__get_actionable_service_id(service_id)
        if secondary:
            response = self.__managed_session(
                HttpMethod.GET,
                self.__get_url_frag(UrlFragType.SERVICE_BASE),
                "Failed to determine if service '%s' exists.",
                '$.data[@.id is "%s"].secondaryLaunchConfigs' % service_id)
        else:
            response = self.__managed_session(
                HttpMethod.GET,
                self.__get_url_frag(UrlFragType.SERVICE_BASE),
                "Failed to determine if service '%s' exists.",
                '$.data[@.id is "%s"].launchConfig' % service_id)
        if response is not None:
            return response
        else:
            return None

    def do_upgrade(self, json_payload, service_id=None):
        self.__logger.trace('Executing do_upgrade....')
        service_id = self.__get_actionable_service_id(service_id)
        self.__set_service_links(service_id)
        response = self.__managed_session(
            HttpMethod.POST,
            self.__get_url_frag(UrlFragType.SERVICE, None, service_id) + '/?action=upgrade',
            "Error while upgrading service id '%s'" % service_id,
            '$.*[@.id is "%s"]' % service_id,
            json_payload
        )
        self.__logger.trace('Received upgrade response (cached)', json.dumps(response,
                                                                             sort_keys=True, indent=2))

    def activate_service(self, service_id=None):
        service_id = self.__get_actionable_service_id(service_id)
        self.wait_for_state('inactive', service_id)
        response = self.__managed_session(
            HttpMethod.POST,
            self.__get_url_frag(UrlFragType.SERVICE, None, service_id) + '/?action=activate',
            "Error while activating service id '%s'" % service_id,
            '$.*[@.id is "%s"]' % service_id
        )
        return response is not None

    def deactivate_service(self, service_id=None):
        service_id = self.__get_actionable_service_id(service_id)
        response = self.__managed_session(
            HttpMethod.POST,
            self.__get_url_frag(UrlFragType.SERVICE, None, service_id) + '/?action=deactivate',
            "Error while deactivating service id '%s'" % service_id,
            '$.*[@.id is "%s"]' % service_id
        )

    def rollback(self, service_id=None):
        self.__logger.info("Rolling back")
        service_id = self.__get_actionable_service_id(service_id)
        response = self.__managed_session(HttpMethod.POST, UrlFragType.SERVICE_BASE + '/' + '/?action=rollback',
                                          "Error while rolling back service with ID = '%s'." % service_id,
                                          '$.*[@.id is "%s"]' % service_id)
        if response is not None:
            return True
        else:
            return False

    def __set_service_links(self, service_id=None):
        if len(self.__service_links['serviceLinks']) > 0:
            service_id = self.__get_actionable_service_id(service_id)
            response = self.__managed_session(HttpMethod.POST,
                                              self.__get_url_frag(UrlFragType.SERVICE, service_id=service_id)
                                              + '/?action=setservicelinks',
                                              "Error while attempting to apply service links to service",
                                              json_payload=self.__service_links
                                              )

    def __get_actionable_stack_id(self, stack_id=None, stack_name=None):
        self.__logger.trace('Executing __get_actionable_stack_id....')
        if stack_id is None and stack_name is not None:
            stack_id = self.__get_stack_id(stack_name)
        elif stack_id is None:
            if self.__stack_id is None:
                self.__stack_id = self.__get_stack_id()
            stack_id = self.__stack_id
        self.__logger.trace('Found actionable stack id: %s' % stack_id)
        return stack_id

    def __get_actionable_service_id(self, service_id=None):
        self.__logger.trace('Executing __get_actionable_service_id....')
        if service_id is None:
            if self.__service_id is None:
                self.__service_id = self.__get_service_id()
            service_id = self.__service_id
        self.__logger.trace('Found actionable service id: %s' % service_id)
        return service_id

    # ==================================================================================================================
    # A function to retrieve and return the environment ID
    # ==================================================================================================================
    # todo: refactor to use managed_session
    def __get_project_id(self):
        self.__logger.trace("Getting project ID for environment %s...." %
                            str(self.__project_name or 'based on security token'))
        projects = {}
        try:
            r = self.__session.get("%s/projects?limit=1000" % self.__api_endpoint)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self.__logger.fatal("Unable to connect to Rancher at %s. Check that you are using the correct URL, "
                                "API version, API key and/or API secret." % self.__api_endpoint)
            self.__session.close()
        else:
            projects = r.json()['data']
            self.__session.close()

        environment_id = None
        if self.__project_name is None:
            self.__logger.trace('No environment provided. Will assume we are using an environment security token....')
            environment_id = projects[0]['id']
            self.__project_name = projects[0]['name']
            self.__logger.debug('Environment Name', self.__project_name)
        else:
            for e in projects:
                if e['id'].lower() == self.__project_name.lower() \
                        or e['name'].lower() == self.__project_name.lower():
                    environment_id = e['id']
                    self.__project_name = e['name']

        if not environment_id:
            if self.__project_name:
                self.__logger.fatal("The '%s' environment doesn't exist in Rancher, or your API "
                                    "credentials don't have access to it" % self.__project_name)
            else:
                self.__logger.fatal("No environment in Rancher matches your request")
        else:
            self.__logger.debug("Project ID", environment_id)
            return environment_id

    # ==================================================================================================================
    # A function to retrieve and return a service ID based on a service reference in the service link argument
    # ==================================================================================================================
    def __get_service_id_from_link_reference(self, service_link_reference):
        # service references are in the form of '<stack>/<service>'
        stack_name, service_name = service_link_reference.split('/')
        return self.__get_service_id(stack_name, service_name)

    # ======================================================================================================================
    # A function to retrieve and return a service ID based on a service reference in the service link argument
    # ======================================================================================================================
    def __get_service_id(self, stack_name=None, service_name=None):
        self.__logger.trace('Executing __get_service_id....')
        service_id = None
        stack_id = self.__get_actionable_stack_id(stack_name=stack_name)
        response = self.__managed_session(
            HttpMethod.GET,
            self.__get_url_frag(UrlFragType.SERVICE_BASE, stack_id),
            "Failed to get ID for service '%s'" % str(service_name or self.__service_name),
            '$.data[@.name is "%s"].id' % str(service_name or self.__service_name))
        if response is not None:
            self.__logger.debug("Service ID", response)
            return response
        else:
            return None

    # ======================================================================================================================
    # A function to retrieve and return a stack ID based on a stack name
    # ======================================================================================================================
    def __get_stack_id(self, stack_name=None):
        self.__logger.trace('Executing __get_stack_id....')
        response = self.__managed_session(
            HttpMethod.GET,
            self.__get_url_frag(UrlFragType.STACK_BASE),
            "Failed to get ID for stack '%s'" % str(stack_name or self.__stack_name),
            '$.data[@.name is "%s"].id' % str(stack_name or self.__stack_name))
        if response is not None:
            return response
        else:
            return None

    def __get_url_frag(self, url_type: UrlFragType, stack_id=None, service_id=None):
        """ URL formatter

        v1      = <api_endpoint>/projects/<id>/environments/<id>/services
        v2-beta = <api_endpoint>/projects/<id>/stacks/<id>/services

        <api_endpoint>/projects/<id>/services/<id>

        :param url_type:
        :return:
        """
        self.__logger.trace('Executing __get_url_frag....')
        stacks_url_fragment = 'ERROR'
        if self.__api_version == 'v1':
            stacks_url_fragment = '/environments'
        elif self.__api_version == 'v2-beta':
            stacks_url_fragment = '/stacks'
        else:
            self.__logger.fatal('Unrecognized API version (%s). Please verify the API version and '
                                'try again.' % self.__api_version)

        self.__logger.trace('Getting url fragment %s for api version %s' % (url_type.name, self.__api_version))
        projects = self.__api_endpoint + '/projects'
        project = projects + '/' + self.__project_id
        stacks = project + stacks_url_fragment
        stack = stacks + '/%s' % str(stack_id or self.__stack_id)
        services = stack + '/services'
        service = project + '/services/%s' % str(service_id or self.__service_id)

        frags = {
            UrlFragType.PROJECT_BASE: projects,
            UrlFragType.PROJECT: project,
            UrlFragType.STACK_BASE: stacks,
            UrlFragType.STACK: stack,
            UrlFragType.SERVICE_BASE: services,
            UrlFragType.SERVICE: service
        }
        return frags.get(url_type)

    def __managed_session(self, method: HttpMethod, url: str, err_msg: str, object_path_query='$.*', json_payload=None):
        response = None
        http_response = None
        try:
            self.__logger.debug('Managed Session Url', url)
            if method is HttpMethod.GET:
                self.__logger.trace('Executing a GET')
                http_response = self.__session.get(url)
            elif method is HttpMethod.POST:
                self.__logger.trace('Executing a POST (payload cached)',
                                    json.dumps(json_payload, sort_keys=True, indent=2))
                http_response = self.__session.post(url, json=json_payload)
            else:
                self.__logger.error("Unknown HTTP method.")
            http_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.__logger.error(err_msg + ": \r\n\t %s" % format(e))
        else:
            self.__logger.trace("Response cached", json.dumps(http_response.json(), sort_keys=True, indent=2))
            try:
                tree = Tree(http_response.json())
                self.__logger.debug("Query", object_path_query)
                response = tree.execute(object_path_query)
                self.__logger.trace("Response cached", json.dumps(response, sort_keys=True, indent=2))
                if response is not None and len(response) < 1:
                    response = None
            except TypeError as te:
                self.__logger.error("TypeError: %s" % format(te))
                self.__logger.trace_dump()
                response = None
            except AttributeError as e:
                self.__logger.error("AttributeError: %s" % format(e))
                self.__logger.trace_dump()
                response = None
            except StopIteration as e:
                self.__logger.error("StopIteration: %s" % format(e))
                self.__logger.trace_dump()
                response = None
            except SyntaxError as e:
                self.__logger.error("SyntaxError: %s" % format(e))
                self.__logger.trace_dump()
                response = None
            except Exception as ex:
                self.__logger.error("Unhandled Exception: %s" % format(type(ex)))
                self.__logger.trace_dump()
                response = None
        finally:
            self.__session.close()
            return response

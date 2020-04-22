import requests


class RancherConnection:
    """
    A class to package current info regarding the Rancher instance we're working with.
    """

    def __init__(self):
        """
        Empty constructor
        """
        self.url = ''
        self.key = ''
        self.secret = ''
        self.api_endpoint = ''
        self.stack_name = ''
        self.service_name = ''
        self.session = requests.Session()
        self.labels = {}

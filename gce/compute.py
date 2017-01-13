from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials


class ComputeApi(object):
    """Google Compute Api.

    https://cloud.google.com/compute/docs/reference/latest/
    """

    def __init__(self, service_account):
        """Initialize response data from service account info """
        if not isinstance(service_account, dict):
            raise ValueError('Not a dict: ' + str(service_account))
        self.project_id = service_account['project_id']
        self.scopes = ['https://www.googleapis.com/auth/compute']
        self.credentials = self._create_credentials(service_account)
        self.service = self._create_compute_service_client()

    def _create_credentials(self, service_account):
        """Create credentials to interate with compute api"""
        return ServiceAccountCredentials.from_json_keyfile_dict(
            service_account, self.scopes)

    def _create_compute_service_client(self):
        """Create compute service client"""
        service = discovery.build(
            'compute', 'v1', credentials=self.credentials,
        )
        return service

    def _get_zones(self):
        response = self.service.zones().list(project=self.project_id).execute()
        zones = response.get('items')
        return zones

    def _get_regions(self):
        response = self.service.regions().list(
            project=self.project_id).execute()
        regions = response.get('items')
        return regions

    def machine_types(self):
        """Returns list of machine types available to project"""
        print self.project_id
        response = self.service.machineTypes().aggregatedList(
            project=self.project_id).execute()
        machine_types = response.get('items')
        return machine_types

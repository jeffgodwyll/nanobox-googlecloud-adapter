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

    def instance(self, name=None, zone=None, machine_type=None):
        """Create an instance associated with the compute engine service

        :type name: str
        :param name: The unique name of the instance.
                     This will be used as the unique ID in nanobox

        :type zone: str
        :param zone: zone the instance will exist in
                     this corresponds to the region in nanobox

        :type machine_type: str
        :param machine_type: machine type, for nanobox this corresponds to the
                             server sizes
        """
        return Instance(client=self, name=name, zone=zone,
                        machine_type=machine_type)


class Instance(object):

    """Compute Engine Instance.

    :type name: str
    :param name: the name of the instance

    :type zone: str
    :param zone: zone the instance will exist in

    :machine_type: string: full or partial URL of the machine type resource
                            to use
                            eg: zones/zone/machineTypes/<machine-type>
    :type machine_type: str
    :param machine_type: machine type, for nanobox this corresponds to the
                             server sizes

    :type status: str
    :param status: status of instance. [PENDING, RUNNING, DONE]
    """

    def __init__(self, client, name, zone, machine_type):
        self.client = client
        self.name = name
        self.machine_type = machine_type
        self.zone = zone
        self.status = None
        self.ssh_key = None

    def _create_instance(self):

        # get ubuntu image
        image_response = self.client.service.images().getFromFamily(
            project='ubuntu-os-cloud', family='ubuntu-1604-lts').execute()
        source_disk_image = image_response['selfLink']

        # configure the machine
        machine_type = "zones/{}/machineTypes/{}".format(
            self.zone, self.machine_type)

        config = {
            'name': self.name,
            'machineType': machine_type,

            'disks': [{
                'boot': True,
                'autoDelete': True,
                'initializeParams': {'sourceImage': source_disk_image}
            }],

            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [{
                    'type': 'ONE_TO_ONE_NAT',
                    'name': 'Nanobox NAT'}]
            }],
            'metadata': {
                'items': [{
                    'key': 'sshKeys',
                    'value': self.ssh_key}]
            }
        }

        resp = self.client.service.instances().insert(
            project=self.client.project_id,
            zone=self.zone,
            body=config).execute()

        return resp

    def create(self):
        return self._create_instance()

    def list_instances(self):
        """Get a list of all instances from all zones in the project"""

        response = self.client.service.instances().aggregatedList(
            project=self.client.project_id).execute()

        zones = response.get('items', {})
        instances = []
        for zone in zones.values():
            for instance in zone.get('instances', []):
                instances.append(instance)

        return instances

    def find_instance(self, id):
        instances = self.list_instances()
        instance = next(
            (instance for instance in instances if instance['name'] == id),
            None)

        return instance

    def delete_instance(self,  instance_id):
        instance = self.find_instance(instance_id)
        if instance:
            zone = self._process_zone_url(instance['zone'])
            return self.client.service.instances().delete(
                project=self.client.project_id,
                zone=zone,
                instance=instance_id).execute()

    def _process_zone_url(self, zone):
        return zone.split('/')[-1]

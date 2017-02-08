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

import json

from flask import Flask, jsonify, request, abort
from gce.compute import ComputeApi


app = Flask(__name__)

META_INSTRUCTIONS = (
    "Download service account json key from: "
    "https://console.developers.google.com/project/_/apiui/credential "
    "Copy its content into nanobox admin page."
)


def client():
    auth_header = request.headers.get('Auth-Service-Account')
    if auth_header:
        try:
            service_account = json.loads(auth_header)
            service = ComputeApi(service_account)
            return service
        except(ValueError, KeyError):
            abort(400, 'Invalid Service Account JSON')

    abort(400, 'Auth-Service-Account header required')


def get_price(zone, name):
    with open('pricelist.json') as f:
        resp = json.load(f)
    pricelist = resp['gcp_price_list']

    # clean up to obtain only the relevant compute engine vms
    vms = (vm for vm in pricelist.keys()
           if vm.startswith('CP-COMPUTEENGINE-VMIMAGE') and
           name.upper() in vm and
           not vm.endswith('PREEMPTIBLE'))
    entry = {k: pricelist[k] for k in vms if k in pricelist}
    # example entry:
    # {u'CP-COMPUTEENGINE-VMIMAGE-N1-STANDARD-8': {u'asia': 0.44,
    #   u'asia-east': 0.44,
    #   u'asia-northeast': 0.5304,
    #   u'cores': u'8',
    #   u'europe': 0.44,
    #   u'gceu': 22,
    #   u'maxNumberOfPd': 16,
    #   u'maxPdSize': 10,
    #   u'memory': u'30',
    #   u'ssd': [0, 1, 2, 3, 4],
    #   u'us': 0.4}}
    # eg:
    # k = CP-COMPUTEENGINE...
    # v = {'asia': 0.44, 'asia-east'.... 'us': 0.4}
    # a = zone or region name, asia
    # b = price, eg 0.44
    price = next(b for k, v in entry.items()
                 for a, b in v.items() if a in zone)
    return price


@app.route('/')
def home():
    return jsonify(
        description='A provider for deploying Nanobox apps to Google Cloud.')


@app.route('/verify', methods=['POST'])
def verify():
    service = client()
    if service:
        return ''
    abort(400, 'invalid auth details')


@app.route('/meta')
def meta():
    return jsonify({
        "id": "gce",
        "name": "Google Compute Engine",
        "server_nick_name": "vm",
        "default_region": "us-central1-a",
        "default_size": "f1-micro",
        "default_plan": "f1-micro",
        "can_reboot": True,
        "can_rename": True,
        "credential_fields": [
            {"key": "service-account", "label": "service account"}],
        "instructions": META_INSTRUCTIONS
    })


@app.route('/catalog')
def catalog():
    with open('catalog.json') as data:
        resp = json.load(data)
    return jsonify(resp)


@app.route('/admin/catalog')
def update_catalog():
    service = client()
    resp = service.machine_types()
    catalog = []
    for zone, machinetypes in resp.items():
        # eg. remove zone from zone/asia-notheast1-c
        zone = zone.split('/')[1]
        plans = []
        for machine in machinetypes['machineTypes']:
            name = machine['name']
            dollars_per_hr = get_price(zone, name)
            dollars_per_mo = int(dollars_per_hr * 24 * 7 * 4)
            memory = machine['memoryMb']
            plan = {
                'name': name,
                'id': name,
                'specs': [{
                    'id': name,
                    'description': machine['description'],
                    'ram': int(memory),
                    'cpu': int(machine['guestCpus']),
                    'disk': int(machine['maximumPersistentDisksSizeGb']),
                    'transfer': 'unlimited',
                    'dollars_per_hr': dollars_per_hr,
                    'dollars_per_mo': dollars_per_mo
                }]
            }
            plans.append(plan)

        info = {
            'id': zone,
            'name': zone,
            'plans': plans
        }
        catalog.append(info)

    with open('catalog.json', 'w') as output:
        json.dump(catalog, output)

    return jsonify(catalog)


@app.route('/keys', methods=['POST'])
def keys():
    service = client()
    data = request.get_json()
    key = data['key']
    try:
        ssh_key = service.set_project_ssh_key(key)
    except ValueError as e:
        abort(400, 'Invalid Key Format. {}'.format(e.message))
    user = ssh_key['user']

    response = jsonify(id=user)
    response.status_code = 201

    return response


@app.route('/keys/<id>')
def keys_id(id):
    service = client()
    key_req = service.get_project_ssh_key(id)
    if not key_req:
        abort(404, 'key with id: `%s` not found' % id)

    protocol, public_key, user = key_req.split(' ')

    key = {}
    key['name'] = user
    key['id'] = user
    key['public_key'] = public_key

    return jsonify(key)


@app.route('/keys/<id>', methods=['DELETE'])
def delete_key(id):
    service = client()
    service.set_project_ssh_key()
    return ('', 200)


@app.route('/servers', methods=['POST'])
def servers():
    service = client()

    zone = request.form.get('region')
    machine_type = request.form.get('size')
    # TODO: name must match the ff regex:
    # (?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)
    name = request.form.get('name')
    ssh_key = request.form.get('ssh_key')

    instance = service.instance(
        name=name, zone=zone, machine_type=machine_type)
    instance.ssh_key = ssh_key
    instance = instance.create()
    instance_url = instance['targetLink']
    id = instance_url.split('/')[-1]

    response = jsonify(id=id)
    response.status_code = 201

    return response


@app.route('/servers/<id>')
def server(id):
    service = client()
    server = service.instance().find_instance(id)
    if server is None:
        abort(404, 'Server with id: `%s` not found' % id)

    details = {}
    details['id'] = server['name']
    details['status'] = server['status']
    details['name'] = server['name']
    network_info = next(
        (interface for interface in server['networkInterfaces']), None)
    details['internal_ip'] = network_info.get('networkIP')
    external_nat = next(
        (access_config for access_config in network_info['accessConfigs']),
        None
    )
    details['external_ip'] = external_nat['natIP']

    return jsonify(details)


@app.route('/servers/<id>', methods=['DELETE'])
def delete_server(id):
    service = client()
    server = service.instance().delete_instance(id)
    if server is None:
        abort(404, 'No Server with id: `%s` was previously ordered. '
              'Cannot cancel non-existing server' % id)
    print 'type of server is: ', type(server)
    print server
    return jsonify(server)


@app.route('/servers/<id>/reboot')
def server_reboot():
    pass


@app.route('/servers/<id>/rename', methods=[])  # PATCH?
def server_rename():
    pass


@app.errorhandler(400)
def bad_request(error=None):
    message = {
        'status': 400,
        'errors': 'Bad request: {}'.format(error.description)
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'errors': 'Not found: {}'.format(error.description)
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


@app.errorhandler(405)
def not_allowed(error=None):
    message = {
        'status': 405,
        'errors': 'Not Allowed: {}'.format(request.method)
    }
    resp = jsonify(message)
    resp.status_code = 405

    return resp


@app.errorhandler(500)
def internal_error(error=None):
    message = {
        'status': 500,
        'errors': 'Internal Server Error: {}'.format(error)
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


if __name__ == '__main__':
    app.run(debug=True)

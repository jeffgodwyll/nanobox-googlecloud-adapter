from flask import Blueprint, jsonify, request, abort

from util import client

server = Blueprint('server', __name__)


@server.route('/servers', methods=['POST'])
def server_create():
    service = client()

    data = request.get_json()

    zone = data['region']
    machine_type = data['size']

    # TODO: name must match the ff regex:
    # (?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)
    name = data['name']
    name = encode_name(name)

    instance = service.instance(
        name=name, zone=zone, machine_type=machine_type)
    instance = instance.create()
    instance_url = instance['targetLink']

    id = instance_url.split('/')[-1]
    id = decode_name(id)

    response = jsonify(id=id)
    response.status_code = 201

    return response


@server.route('/servers/<id>')
def server_get(id):
    service = client()
    id = encode_name(id)
    server = service.instance().find_instance(id)
    if server is None:
        abort(404, 'Server with id: `%s` not found' % id)

    details = {}
    details['id'] = server['name']

    status = server['status']
    if status == 'RUNNING':
        details['status'] = 'active'
    else:
        details['status'] = status

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


@server.route('/servers/<id>', methods=['DELETE'])
def delete_server(id):
    service = client()
    id = encode_name(id)
    server = service.instance().delete_instance(id)
    if server is None:
        abort(404, 'No Server with id: `%s` was previously ordered. '
              'Cannot cancel non-existing server' % id)
    return ('', 200)


@server.route('/servers/<id>/reboot')
def server_reboot():
    pass


@server.route('/servers/<id>/rename', methods=[])  # PATCH?
def server_rename():
    pass


def encode_name(name):
    return name.replace('.', '-dot-')


def decode_name(name):
    return name.replace('-dot-', '.')

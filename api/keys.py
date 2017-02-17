from flask import Blueprint, jsonify, request, abort

from util import client


keys = Blueprint('keys', __name__)


@keys.route('/keys', methods=['POST'])
def key_new():
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


@keys.route('/keys/<id>')
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


@keys.route('/keys/<id>', methods=['DELETE'])
def delete_key(id):
    service = client()
    service.set_project_ssh_key()
    return ('', 200)

import json
from flask import request, abort

# from gce import ComputeApi

from gce import ComputeApi


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

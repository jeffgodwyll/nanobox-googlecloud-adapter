from flask import Blueprint, request, jsonify

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(400)
def bad_request(error=None):
    message = {
        'status': 400,
        'errors': 'Bad request: {}'.format(error.description)
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@errors.app_errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'errors': 'Not found: {}'.format(error.description)
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


@errors.app_errorhandler(405)
def not_allowed(error=None):
    message = {
        'status': 405,
        'errors': 'Not Allowed: {}'.format(request.method)
    }
    resp = jsonify(message)
    resp.status_code = 405

    return resp


@errors.app_errorhandler(500)
def internal_error(error=None):
    message = {
        'status': 500,
        'errors': 'Internal Server Error: {}'.format(error)
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp

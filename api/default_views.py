from flask import Blueprint, jsonify, abort

from util import client


default_views = Blueprint('default', __name__)

META_INSTRUCTIONS = (
    "Download service account json key from: "
    "https://console.developers.google.com/project/_/apiui/credential "
    "Copy its content into nanobox admin page."
)


@default_views.route('/')
def home():
    return jsonify(
        description='A provider for deploying Nanobox apps to Google Cloud.')


@default_views.route('/verify', methods=['POST'])
def verify():
    service = client()
    if service:
        return ''
    abort(400, 'invalid auth details')


@default_views.route('/meta')
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

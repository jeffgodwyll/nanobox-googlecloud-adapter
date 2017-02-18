from flask import Blueprint, jsonify, abort

from util import client


default_views = Blueprint('default', __name__)

META_INSTRUCTIONS = (
    """
    Sign into the Google Cloud Developers' Console & create a project.
    Enable the Compute Engine API by going to the API Management page of the
    created project.

    Download your service account JSON key file by doing the following:

    <b>1.</b> Go to
    <a href="https://console.developers.google.com/project/_/apiui/credential"
    target="_blank">the credentials tab</a> on the API Management page.

    <b>2.</b> Select <b>Service account key</b> from the
    <em>new credentials</em> menu

    <b>3.</b> Select a service account, the JSON key type and
    <b>click create</b>.

    Keep the JSON file safe.

    We will copy the contents of the JSON key file into the
    <b>Service Account</b> field on the next page.

    """
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

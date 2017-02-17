import json

from flask import Blueprint, jsonify

from util import client

catalog = Blueprint('catalog', __name__)


@catalog.route('/catalog')
def catalog_list():
    with open('catalog.json') as data:
        resp = json.load(data)
    return jsonify(resp)


@catalog.route('/catalog/update')
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

#    Copyright 2015 Mirantis, Inc
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import csv
import datetime

from keystoneclient.auth.identity import v2
from keystoneclient import session
from keystoneclient.v2_0 import client
from novaclient import client as nova_cli


URL = 'http://localhost:5000/v2.0'
USER = 'admin'
PASSWORD = 'test'
TENANT = 'admin'
BASE_DIR = '/var/log/reports/'


def main():
    auth = v2.Password(auth_url=URL,
                       username=USER,
                       password=PASSWORD,
                       tenant_name=TENANT)
    sess = session.Session(auth=auth)
    cli = nova_cli.Client(2, session=sess)
    keystone = client.Client(auth_url=URL,
                             username=USER,
                             password=PASSWORD,
                             tenant_name=TENANT)
    tenants = dict((r.id, r.name) for r in keystone.tenants.list())
    ret = []
    instances = cli.servers.list(search_opts={'all_tenants': 1})
    instances_per_tenants = {}
    for i in instances:
        if i.tenant_id not in instances_per_tenants:
            instances_per_tenants[i.tenant_id] = [i]
        else:
            instances_per_tenants[i.tenant_id].append(i)
    #hypervisorX,Tenant_name,Instance_name1,ip_addresses(all)
    for tenant in sorted(instances_per_tenants):
        instances = instances_per_tenants[tenant]
        for i in instances:
            instance_dict = i.to_dict()
            hypervisor = instance_dict['OS-EXT-SRV-ATTR:hypervisor_hostname']
            instance_name = i.name
            networks = []
            for addresses in i.networks.values():
                networks.extend(addresses)
            tenant_name = tenants[tenant]
            flavor = cli.flavors.get(i.flavor['id'])
            flavor_str = "%s (ram %s, vcpus %s)" % (
                flavor.name, flavor.ram, flavor.vcpus)
            ret.append((hypervisor,
                        tenant_name,
                        instance_name,
                        i.status,
                        flavor_str,
                        ','.join(networks)))
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    f_name = BASE_DIR + 'instances_hypervisors_%s.csv' % today
    with open(f_name, 'wb') as f:
        wr = csv.writer(f, quoting=csv.QUOTE_ALL)
        for row in ret:
            wr.writerow(row)
    print "Result was stored in ", f_name

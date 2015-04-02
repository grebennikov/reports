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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from cinderclient import client as cinder_client
from keystoneclient.auth.identity import v2
from keystoneclient import session
from keystoneclient.v2_0 import client
from neutronclient.neutron import client as neutron_client
from novaclient import client as nova_cli


URL = 'http://localhost:5000/v2.0'
USER = 'admin'
PASSWORD = 'test'
TENANT = 'admin'
BASE_DIR = '/var/log/reports/'
OWNER_ROLE = 'admin'
FROM = 'REPORT_QOUTAS@openstack.com'
HEAD = """
<html>
 <head>
  <meta charset="utf-8">
  <style>
   td {
    font-family: 'Times New Roman', Times, serif;
    font-size: 10pt;
    padding: 5px;
   }
  </style>
 </head>
 <body>
 <table border="1" cellpadding="0" cellspacing="0">
   <tr>
      <td>component</td>
      <td align='center'>qouta type</td>
      <td align='center'>value</td>
 </tr>
"""
FOOT = '</table><body></html>'


CINDER_FIELDS = [
    'gigabytes',
    'gigabytes_lvmdriver-1',
    'snapshots',
    'snapshots_lvmdriver-1',
    'volumes',
    'volumes_lvmdriver-1',

]


def main():
    auth = v2.Password(auth_url=URL,
                       username=USER,
                       password=PASSWORD,
                       tenant_name=TENANT)
    sess = session.Session(auth=auth)
    _nova_cli = nova_cli.Client(2, session=sess)
    _cinder_cli = cinder_client.Client(2, session=sess)
    _neutron_cli = neutron_client.Client(2.0, session=sess)
    keystone = client.Client(auth_url=URL,
                             username=USER,
                             password=PASSWORD,
                             tenant_name=TENANT)
    users = keystone.users.list()
    tenants = dict((r.id, r.name) for r in keystone.tenants.list())
    s = smtplib.SMTP()
    s.connect()
    for tenant_id, tenant_name in tenants.iteritems():
        rows = []
        user_owners = {}
        for user in users:
            roles = user.list_roles(tenant_id)
            owner_role = [r for r in roles if r.name == OWNER_ROLE]
            if owner_role:
                email = getattr(user, 'email', None)
                if email is not None:
                    user_owners[user.name] = email
        nova_quotas = _nova_cli.quotas.get(tenant_id)
        cinder_quotas = _cinder_cli.quotas.get(tenant_id)

        neutron_quotas = _neutron_cli.show_quota(tenant_id)
        for k, v in nova_quotas.to_dict().iteritems():
            if k != 'id':
                rows.append(('NOVA', k, str(v)))
        for k in CINDER_FIELDS:
            rows.append(('CINDER', k, str(getattr(cinder_quotas, k))))
        for k, v in neutron_quotas['quota'].iteritems():
            rows.append(('NEUTRON', k, str(v)))
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        f_name = BASE_DIR + '%s_tenant_quotas_%s.csv' % (tenant_name, today)
        with open(f_name, 'wb') as f:
            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
            for row in rows:
                wr.writerow(row)
        print "Result was stored in ", f_name
        if user_owners:
            body = ''
            for (component, name, value) in rows:
                body += "<tr><td>%s</td><td align='center'>%s</td>"\
                        "<td align='center'>%s</td></tr>" % (component,
                                                             name,
                                                             value)
            message = ''.join((HEAD, body, FOOT))
            msg = MIMEMultipart()
            msg['Subject'] = 'Tenant quotas report (%s)' % tenant_name
            msg['From'] = FROM
            msg['To'] = ','.join(user_owners.values())
            msg.set_charset('utf-8')
            msg.set_default_type("text/html")
            msg.attach(MIMEText(message, 'html', _charset='utf-8'))
            for email in user_owners.values():
                s.sendmail(FROM, email, msg.as_string())
    s.quit()

==============
REPORTS
==============

Overview
--------

Report instances_hypervisors store instances info sorted by tenants.
Openstack credantials and folder with csv reports are hardcoded.

Report tenants_qouta return nova, cinder, neutron quotas per tenants.
Openstack credantials and folder with csv reports are hardcoded.

Changed settings
----------------

Each report contains creds:

.. code-block:: bash

  URL = 'http://localhost:5000/v2.0'
  USER = 'admin'
  PASSWORD = 'test'
  TENANT = 'admin'
  BASE_DIR = '/var/log/isrm/'

Usage
------

.. code-block:: bash

  python instances_hypervisors.py
  Result was stored in  /var/log/reports/instances_hypervisors_2015-03-31.csv

.. code-block:: bash

  python tenants_qouta.py
  Result was stored in  /var/log/reports/demo_tenant_quotas_2015-03-31.csv
  Result was stored in  /var/log/reports/alt_demo_tenant_quotas_2015-03-31.csv
  Result was stored in  /var/log/reports/service_tenant_quotas_2015-03-31.csv
  Result was stored in  /var/log/reports/invisible_to_admin_tenant_quotas_2015-03-31.csv
  Result was stored in  /var/log/reports/admin_tenant_quotas_2015-03-31.csv

Limitations
------------

Each report needs in access to manage network.

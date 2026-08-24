#!/usr/bin/env python3
"""
connection.py
-------------
Shared MORIA database connection used by every example script in this
directory. Each example imports `db`, `storage`, `query`, and `admin`
from here instead of re-initializing the connection itself.

Update `moria_path` and the Database() arguments below to match your
own environment before running any of the examples.
"""

import sys

# NOTE: location of the MORIA API package on your system
moria_path = ''
sys.path.insert(0, moria_path)

from database import Database, StorageAPI, QueryAPI, AdminAPI

# Initializes the connection to the server containing the data. server_ip is
# set to None because this assumes the script is running on the same server
# as MongoDB. If not, replace with the server's IP address.
db = Database(db_name='moria_test', server_ip='localhost', user_type='read_write')
storage = StorageAPI(db)
query = QueryAPI(db)
admin = AdminAPI(db)

#!/usr/bin/env python3
"""
query_examples.py
--------------------
Query API examples: building filter pipelines and running them.

Value or range query dictionaries are submitted to the current filter
pipeline via query_data_value()/query_data_range(). Multiple calls can
be chained and are treated as additional (AND'd) filters. Call
clear_query() to reset the pipeline between examples.

Using make_dict=True with run_query() returns a user-friendly
dictionary keyed by device_name; otherwise it returns a raw MongoDB
cursor. Range queries must be a numeric [start, end] list; value
queries must be a list even for a single value.

Requires storage_examples.py to have been run first.

Covers:
  1. Single value query          -> fetch and view one image document
  2. Range query                 -> fetch_related_data across devices
  3. Combined value + range query -> stacked filters
"""

from connection import query

# ----------------------------------------------------------------------------
# 1. Single value query: one device_name + shot_number -> view its image
# ----------------------------------------------------------------------------
device_name = 'basler_1'
value_query_dict = {'metadata': {'device_name': [device_name],
                                  'shot_number': [1]
                                  }
                     }

query.query_data_value(value_query_dict)
raw_res, proc_res = query.run_query(fetch_related_data=False, make_dict=True)

print('\nEXAMPLE 1: image document')
print('----------------------------------')
print(raw_res[device_name][0]['metadata'])   # document metadata
mongo_img = raw_res[device_name][0]['data']  # actual file in MongoDB format
query.view_image(mongo_img)

query.clear_query()
print('')


# ----------------------------------------------------------------------------
# 2. Range query with fetch_related_data=True: pulls in other devices'
#    data for the same matching shots, not just the filtered device.
# ----------------------------------------------------------------------------
range_query_dict = {'metadata': {'shot_number': [1, 3]},
                     'data': {'meas1': [0.5, 1.5]}
                     }

query.query_data_range(range_query_dict)
raw_res, proc_res = query.run_query(fetch_related_data=True, make_dict=True)

# Output: should include gauge_1 and basler_1 documents corresponding to
# shots 2 & 3.
for device in raw_res:
    device_list = raw_res[device]
    print(f'\nEXAMPLE 2: {device} documents')
    print('----------------------------------')
    for doc in device_list:
        print(doc)

for diag in proc_res:
    diag_list = proc_res[diag]
    print(f'\nEXAMPLE 2: {diag} analysis')
    print('----------------------------------')
    for doc in diag_list:
        print(doc)

query.clear_query()
print('')


# ----------------------------------------------------------------------------
# 3. Combined value + range query: filters stack as additional (AND'd)
#    criteria in the same pipeline.
# ----------------------------------------------------------------------------
value_query_dict = {'metadata': {'instrument': ['GAUGE']}}
range_query_dict = {'metadata': {'shot_number': [3, 4]}}

query.query_data_value(value_query_dict)
query.query_data_range(range_query_dict)
raw_res, proc_res = query.run_query(fetch_related_data=False, make_dict=True)

# Output: should be the gauge_1 documents corresponding to shots 3 & 4
for device in raw_res:
    device_list = raw_res[device]
    print(f'\nEXAMPLE 3: {device} documents')
    print('----------------------------------')
    for doc in device_list:
        print(doc)

query.clear_query()

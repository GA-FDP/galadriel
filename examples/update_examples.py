#!/usr/bin/env python3
"""
update_examples.py
---------------------
Administration API examples for updating/inserting new information
into previously archived data.

CAUTION: the update option CAN/WILL overwrite field data and is
irreversible. Be very careful when choosing filters -- make them as
specific as possible, or keep them to individual documents (shot
number, device name), to avoid overwriting vast quantities of
documents.

Three separate update commands:
  replace  Replaces the value in the document(s) with the value in
           the update dictionary where the fields match.
  insert   Adds a new field/value pair to the document(s). If the
           field exists it overwrites the current entry.
  append   Appends the value found in the update dictionary to the
           document(s) dict/list value where the fields match.

The update dictionary has the same structure as the filter
dictionaries, EXCEPT the entry value is NOT required to be a list --
it can be an int/float, an array of values, a dictionary, or whatever
else.

Requires storage_examples.py to have been run first. Run each example
separately -- later examples build on documents created by earlier
ones in this same file, so run them top to bottom.
"""

from connection import admin

# ----------------------------------------------------------------------------
# 1. replace: overwrite the experiment name for the specific shots.
#    As with query examples, additional filters can be stacked.
#    Output: should return "3 documents updated." | 1 camera doc and 2
#    acquisition docs
# ----------------------------------------------------------------------------
value_filter_dict = {}
range_filter_dict = {'metadata': {'shot_number': [3, 4]}}
update_dict = {'metadata': {'experiment': 'TEST_EXP2'}}

admin.update_doc(update_dict, value_filter_dict, range_filter_dict, command='replace')


# ----------------------------------------------------------------------------
# 2. insert: add a new array measurement as a new data field in a
#    single document [shot number and device_name].
#    Output: should return "1 documents updated." | 1 acquisition doc
# ----------------------------------------------------------------------------
value_filter_dict = {'metadata': {'device_name': ['gauge_1'],
                                   'shot_number': [5]
                                   }
                      }
range_filter_dict = {}
update_dict = {'data': {'meas_array': [1, 2, 3, 4, 5, 6]}}

admin.update_doc(update_dict, value_filter_dict, range_filter_dict, command='insert')


# ----------------------------------------------------------------------------
# 3. append: append a dictionary describing the field added in example 2.
#    Output: should return "1 documents updated."
# ----------------------------------------------------------------------------
update_dict = {'metadata': {'append_to': 'dict',  # 'list' or 'dict'
                             'data_info': {'meas_array': {
                                 'data_type': 'array[int]',
                                 'units': 'seconds',
                                 'description': 'example measurement array'}
                             }
                             }
                }

admin.update_doc(update_dict, value_filter_dict, range_filter_dict, command='append')


# ----------------------------------------------------------------------------
# 4. add_note_to_doc: convenience method that appends a comment (with
#    automatic timestamp and author) to a single document's `notes` list.
#    Output: should return "1 documents updated."
# ----------------------------------------------------------------------------
admin.add_note_to_doc(4, 'gauge_1', 'test note describing some additional information')

# NOTE: equivalent to running
# update_dict = { 'metadata' : { 'append_to' : 'list',
#                                'notes' : { 'created_by' : pwd.getpwuid(os.getuid()).pw_name,
#                                            'date' : datetime.now(),
#                                            'content' : 'Added a description about the new field'
#                                          }
#                              }
#               }
# admin.update_doc(update_dict, value_filter_dict, range_filter_dict, command='append')

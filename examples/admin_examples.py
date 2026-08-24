#!/usr/bin/env python3
"""
admin_examples.py
------------------
Administration API examples: one-time setup of the experiment,
instruments, and diagnostics required before any data can be archived.

Run this once against a fresh database before trying the storage,
query, or update examples.
"""

from connection import query, admin

# ----------------------------------------------------------------------------
# Setting up the experiment, instruments, and diagnostics
# ----------------------------------------------------------------------------

# Set a default experiment name. This can be called from any code connected
# to the database.
admin.set_experiment(name='TEST_EXP')

# Only add a couple instruments for this example (make as general as needed
# for your own experiment).
admin.add_instrument(instrument='GAUGE', gridfs_bool=False)
admin.add_instrument(instrument='CAMERA', gridfs_bool=True)
admin.add_diagnostic(diagnostic='SAMPLE_OUTPUT')

# Print the current entries in the instruments/diagnostics collections.
# Should match the inputs above.
print(f'{query.get_experiment()}')
inst_info = query.hardware_info('instruments', print_list=True)
diag_info = query.hardware_info('diagnostics', print_list=True)

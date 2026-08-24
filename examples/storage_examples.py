#!/usr/bin/env python3
"""
storage_examples.py
---------------------
Storage API examples: archiving different types of data into the
database. Usually different device data would be archived within
different control codes simultaneously for the same laser pulse
(shot); here everything is archived in serial for explanatory purposes.

Requires admin_examples.py to have been run first (GAUGE/CAMERA
instruments and SAMPLE_OUTPUT diagnostic must already be registered).

Covers:
  1. Scalar/array data from a simple device      -> `acquisitions`
  2. Image data from a camera (GridFS)            -> `fs.files`/`fs.chunks`
  3. Per-shot processed/diagnostic analysis       -> `processed_data`
  4. Batch-level average over a range of shots    -> `processed_data`
"""

import io
from copy import deepcopy
from datetime import datetime
from random import uniform

from PIL import Image

from connection import query, storage


def image_to_bytes(image_path):
    """Converts an image to bytes."""
    with Image.open(image_path) as img:
        byte_arr = io.BytesIO()
        img.save(byte_arr, format=img.format)
        return byte_arr.getvalue()


# ----------------------------------------------------------------------------
# 1. Scalar/array data -- Device 1: gauge_1  (-> acquisitions)
# ----------------------------------------------------------------------------
# Universal metadata REQUIRED for every device that stores data into the
# acquisitions collection. Any number of fields can be added to these
# dictionaries; these are just the required ones.
data = {}
metadata = {'shot_number': '',        # UNIQUE shot (pulse) indicator
            'experiment': query.get_experiment(),
            'trigger_timestamp': '',  # Time in ISODate format when the acquisition is initiated
            'archive_timestamp': '',  # Time when the data is archived
            'instrument': '',
            'diagnostic': '',         # Diagnostic the device is tied to for this acquisition
            'device_name': '',        # UNIQUE device identifier
            'data_info': {},          # Describes the fields with data
            'notes': []               # Contains individual document comments
            }

gauge1_data, gauge1_metadata = deepcopy(data), deepcopy(metadata)
for shot in range(1, 6):
    # Simulated gauge measurements
    gauge1_data['meas1'] = shot * .37
    gauge1_data['meas2'] = (shot - 1) * .68

    gauge1_metadata['shot_number'] = shot
    gauge1_metadata['trigger_timestamp'] = datetime.now()
    gauge1_metadata['device_name'] = 'gauge_1'
    gauge1_metadata['instrument'] = 'GAUGE'          # MUST exist in instruments collection
    gauge1_metadata['diagnostic'] = 'SAMPLE_OUTPUT'  # MUST exist in the diagnostics collection
    gauge1_metadata['data_info'] = {'meas1': {'data_type': 'float',
                                               'units': 'seconds',
                                               'description': 'example measurement 1'
                                               },
                                     'meas2': {'data_type': 'float',
                                               'units': 'Coulombs',
                                               'description': 'example measurement 2'
                                               }
                                     }
    data_struct = {'data': gauge1_data, 'metadata': gauge1_metadata}
    try:
        storage.insert_data(data_struct)
    except Exception as e:
        print(e)


# ----------------------------------------------------------------------------
# 2. Image data -- Device 2: basler_1  (-> GridFS)
# ----------------------------------------------------------------------------
# Expects sample images in a local sample_images/ folder: forest.jpg,
# m83.tif, mountain.jpg.
basler1_data, basler1_metadata = deepcopy(data), deepcopy(metadata)
for shot in range(1, 4):
    image_path = 'sample_images'
    if shot == 1:
        file_name = 'forest.jpg'
    if shot == 2:
        file_name = 'm83.tif'
    if shot == 3:
        file_name = 'mountain.jpg'

    basler1_metadata['file_name'] = file_name
    basler1_data['buffer'] = image_to_bytes(f'{image_path}/{file_name}')

    basler1_metadata['shot_number'] = shot
    basler1_metadata['trigger_timestamp'] = datetime.now()
    basler1_metadata['device_name'] = 'basler_1'
    basler1_metadata['instrument'] = 'CAMERA'         # MUST exist in the instruments collection
    basler1_metadata['diagnostic'] = 'SAMPLE_OUTPUT'  # MUST exist in the diagnostics collection
    basler1_metadata['data_info'] = {'image': {'data_type': 'GridOut',  # GridFS file output
                                                'units': '',
                                                'file_type': file_name[-3:],
                                                'description': 'recorded image sharded by GridFS'
                                                }
                                      }
    data_struct = {'data': basler1_data, 'metadata': basler1_metadata}
    try:
        storage.insert_data(data_struct)
    except Exception as e:
        print(e)


# ----------------------------------------------------------------------------
# 3. Per-shot processed data -- Diagnostic 1: diag_1  (-> processed_data)
# ----------------------------------------------------------------------------
# Universal metadata REQUIRED for every device that stores intermediate
# analysis into the processed_data collection.
p_data = {}
p_metadata = {'shot_number': '',        # UNIQUE shot (pulse) indicator
              'experiment': query.get_experiment(),
              'archive_timestamp': '',  # Time when the data is archived
              'data_info': {},          # Describes the fields with data
              'notes': []               # Contains individual document comments
              }

diag1_data, diag1_metadata = deepcopy(p_data), deepcopy(p_metadata)
exp_meas = []
for shot in range(1, 6):
    # Simulated diagnostic analysis
    diag1_data['diag_analysis1'] = shot * uniform(0, 1)
    diag1_data['diag_analysis2'] = (shot - 1) * uniform(0, 1)
    exp_meas.append(diag1_data['diag_analysis1'])

    diag1_metadata['shot_number'] = shot
    diag1_metadata['diagnostic'] = 'SAMPLE_OUTPUT'  # REQUIRED & must exist in the diagnostics collection
    diag1_metadata['data_info'] = {'meas1': {'data_type': 'float',
                                              'units': 'seconds',
                                              'description': 'example measurement 1'
                                              },
                                    'meas2': {'data_type': 'float',
                                              'units': 'Coulombs',
                                              'description': 'example measurement 2'
                                              }
                                    }
    data_struct = {'data': diag1_data, 'metadata': diag1_metadata}
    try:
        storage.insert_data(data_struct, True)  # processed data flag
    except Exception as e:
        print(e)

    # --------------------------------------------------------------------
    # 4. Batch-level average over shots 1-4  (-> processed_data)
    # --------------------------------------------------------------------
    if shot == 4:
        # Experimental analysis 1 -- proc_1
        proc1_data, proc1_metadata = deepcopy(p_data), deepcopy(p_metadata)
        proc1_data['exp_raw_data1'] = exp_meas
        proc1_data['exp_analysis1'] = sum(exp_meas) / len(exp_meas)  # average over shot range

        proc1_metadata['shot_number'] = shot
        proc1_metadata['shot_range'] = [1, shot]
        proc1_metadata['process'] = 'experimental_average'  # REQUIRED
        proc1_metadata['data_info'] = {'analysis1': {'data_type': 'float',
                                                       'units': 'seconds',
                                                       'description': 'average over shot range'
                                                       }}
        data_struct = {'data': proc1_data, 'metadata': proc1_metadata}
        try:
            storage.insert_data(data_struct, True)  # processed data flag
        except Exception as e:
            print(e)

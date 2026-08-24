---
name: moria-instrument-class
description: This skill should be used when the user asks to "create an instrument class", "add a new instrument", "integrate a new device", "write a class for [instrument name]", "add [device] to the control system", or "register a new instrument/diagnostic". Guides the full workflow for creating a GALADRIEL instrument class, registering it in the database, wiring it into the control system, and verifying it works.
version: 1.0.0
---

# MORIA Instrument Class Integration Skill

This skill implements the expert workflow for creating and integrating a new instrument or diagnostic into the GALADRIEL control system. Follow all seven steps in order.

## Project Structure Reference

```
galadriel/galadriel/
├── instruments/
│   ├── interface.py                  # GaladrielInstrument base class (Linux)
│   ├── <new_instrument>.py           # New Linux instrument class goes here
│   └── windows_insts/
│       ├── interface.py              # GaladrielInstrument base class (Windows)
│       └── <new_instrument>/
│           └── <new_instrument>.py   # New Windows instrument class goes here
├── diagnostics/
│   ├── interface.py                  # Diagnostic base class
│   └── <new_diagnostic>.py          # New diagnostic class goes here (if needed)
└── control/
    ├── control.config                # Device configuration file
    └── control_setup/
        ├── acquisition_init.py       # Wire in acquisition instruments here
        ├── actuator_init.py          # Wire in actuator instruments here
        └── diagnostics_init.py       # Wire in diagnostic classes here
```

## Base Class Contract (`GaladrielInstrument`)

All instrument classes must subclass `GaladrielInstrument` and implement three abstract methods:

| Method | Purpose |
|---|---|
| `acquire()` | Read data from the instrument |
| `adjust(*args, **kwargs)` | Send a command / control the instrument (pass if acquisition-only) |
| `archive(**kwargs)` | Write the assembled `data_struct` to the MORIA database |

The base class provides:
- `self.db`, `self.storage`, `self.query`, `self.admin` — MORIA API handles
- `self.data` — empty dict for data payload
- `self.metadata` — skeleton dict with all required MORIA fields pre-populated as empty strings

**Windows vs. Linux**: Use `windows_insts/interface.py` (path `C:\moria`) for instruments running on the dedicated Windows laptop (Fastlite devices, Thorlabs cameras, etc.). Use `instruments/interface.py` (path `/moria`) for instruments running on the Linux control server.

---

## Step 1 — Create the Instrument Class

Read the existing Wizzler class at `galadriel/galadriel/instruments/windows_insts/wizzler/wizzler.py` as the canonical template for file-watching/trigger-polling Windows instruments. For Linux acquisition instruments, read a comparable class (e.g., `tekscope.py`, `basler_camera.py`).

Build the new class following this pattern:

```python
# system
import os
import sys
from datetime import datetime, timezone

# GALADRIEL control interface (adjust path for Linux vs. Windows)
sys.path.insert(0, 'C:\\galadriel')   # or '/galadriel' on Linux
from interface import GaladrielInstrument

class NewInstrument(GaladrielInstrument):
    def __init__(self):
        super().__init__()

        # Populate fixed metadata fields
        self.metadata['experiment']   = self.query.get_experiment()
        self.metadata['instrument']   = 'INSTRUMENT_TYPE'   # must exist in instruments collection
        self.metadata['diagnostic']   = 'DIAGNOSTIC_NAME'   # must exist in diagnostics collection
        self.metadata['device_name']  = 'device_name_0'     # unique identifier
        self.metadata['data_info']    = self._data_info()
        self.metadata['notes']        = []

        # Optional: device-specific metadata (manufacturer, serial, etc.)
        self.metadata['manufacturer'] = 'manufacturer_name'

        self.data_struct = {'data': self.data, 'metadata': self.metadata}

        # Set file paths or connection parameters
        self.data_dir = 'C:/path/to/data/'

    @staticmethod
    def _data_info():
        return {
            'field_a': {'data_type': 'float',        'units': 'unit', 'description': '...'},
            'field_b': {'data_type': 'array[float]', 'units': 'unit', 'description': '...'},
        }

    def read_files(self, filepath):
        # Parse the instrument's output file format
        # Return a dict matching the keys in _data_info()
        pass

    def acquire(self):
        # Main acquisition loop (trigger polling or file-watching)
        # Call self.archive() after each successful acquisition
        pass

    def adjust(self): pass  # pass if acquisition-only

    def archive(self):
        self.data['field_a'] = self.field_a_value
        self.data['field_b'] = self.field_b_value

        self.metadata['shot_number']        = self.shot_number
        self.metadata['trigger_timestamp']  = self.trig_time
        self.metadata['archive_timestamp']  = datetime.now(timezone.utc)

        self.storage.insert_data(self.data_struct)
```

**Key decisions to make for each new instrument:**
- Does it run on Windows or Linux? → Determines which `interface.py` to import and where the file lives.
- Is it acquisition-only, actuator-only, or both? → `adjust()` can be `pass` for acquisition-only.
- Does it watch a directory for new files (like Wizzler), poll a hardware trigger, or connect via socket/serial? → Determines the `acquire()` loop structure.
- Does any data field exceed 16 MB? → If yes, set `gridfs=True` when registering the instrument and store data under the `buffer` key in `self.data`.

---

## Step 2 — Register Instrument and Diagnostic in the Database

Before the class can archive data, the `instrument` and `diagnostic` tags must exist in the `instruments` and `diagnostics` collections.

**Check first:**
```python
from database import Database, AdminAPI, QueryAPI
db = Database('galadriel')
admin = AdminAPI(db)
query = QueryAPI(db)

query.hardware_info('instruments', print_list=True)
query.hardware_info('diagnostics', print_list=True)
```

**Add if missing:**
```python
admin.add_instrument('INSTRUMENT_TYPE', gridfs_bool=False)  # True if data > 16 MB
admin.add_diagnostic('DIAGNOSTIC_NAME')
```

Use **UPPERCASE with underscores** to match the GALADRIEL naming convention (e.g., `PULSE_RECONSTRUCTOR`, `SPECTRAL_PHASE`). Check the existing entries and suggest names consistent with what is already registered before adding new ones.

---

## Step 3 — Create a Diagnostic Class (if needed)

A diagnostic class is required when the instrument's data feeds into a post-processed result stored in `processed_data`. If the instrument only archives raw acquisitions, skip this step.

Diagnostic classes live in `galadriel/galadriel/diagnostics/` and follow the pattern in `diagnostics/interface.py`. They depend on one or more acquisition classes passed in at initialization:

```python
class NewDiagnostic:
    def __init__(self, acq_devices: list, acq_class):
        self.acq_devices = acq_devices
        self.acq_class   = acq_class

    def process(self):
        # Read from acq_class.data, compute result, archive to processed_data
        pass
```

Register the diagnostic in `diagnostics_init.py` by adding an `elif` branch:
```python
elif 'new_diagnostic' in diag_name:
    from galadriel.diagnostics import new_diagnostic
    obj = new_diagnostic.NewDiagnostic(acq_dev, acq_classes[0])
```

---

## Step 4 — Wire into the Control System

**4a. Add to `acquisition_init.py` or `actuator_init.py`**

For a new acquisition instrument, add an `elif` branch in `init_acquirers()` in `galadriel/galadriel/control/control_setup/acquisition_init.py`:

```python
elif 'new_instrument' in dev_name:
    from galadriel.instruments import new_instrument
    cfg = setup_params[dev_name]
    inst = new_instrument.NewInstrument(cfg['param_a'], cfg['param_b'])
    acquisition_dict[dev_name] = Acquisition_Info(inst)
```

For a Windows instrument running remotely (like the Wizzler, which runs its own loop on a separate laptop), no entry in `acquisition_init.py` is needed — the class runs as a standalone script on the remote machine.

For a new actuator, add an `elif` branch in `init_actuators()` in `actuator_init.py` following the same pattern.

**4b. Add to `control.config`**

Add the device name to the appropriate list in the `[general]` section:
```ini
# For an acquirer:
acqs_to_use=existing_device;new_instrument_0;

# For an actuator:
acts_to_use=existing_actuator;new_instrument_0;
```

Add a device-specific configuration block:
```ini
[new_instrument_0]
# Connection / hardware parameters
ip_address="169.254.X.X"    # or serial_number, port, etc.
# Archive tags
diag=DIAGNOSTIC_NAME
# Any other device-specific params
param_a=value;
```

If a diagnostic class was created, also add it to `diags_to_use` and add a `[diagnostic_name]` section:
```ini
diags_to_use=existing_diag;new_diagnostic;

[new_diagnostic]
acq_device=new_instrument_0;
# Any calibration or ROI parameters
```

---

## Step 5 — Verify Basic Connectivity

Before running a full experimental loop, confirm the instrument can be reached:

- **Network instruments**: ping the IP, confirm the port responds.
- **Serial/USB instruments**: confirm the device appears on the expected COM port or `/dev/ttyUSB*`.
- **File-watching instruments**: confirm the data directory exists and is writable, and that the instrument software is running and writing files to the expected location.
- **Windows remote instruments**: confirm SSH access to the host computer and that the GALADRIEL and MORIA paths are correct in the class file.

Log the outcome and fix connection issues before proceeding.

---

## Step 6 — Verify Acquisition and Archival

Run a minimal test to confirm data flows end-to-end:

1. Instantiate the class directly (outside the full control loop).
2. Call `acquire()` for a single shot or trigger it manually.
3. Confirm `self.data` is populated with the expected fields.
4. Call `archive()` manually with a known test shot number.
5. Query the database to confirm the document was written with correct metadata:

```python
from database import Database, QueryAPI
db = Database('galadriel')
query = QueryAPI(db)
query.query_data_value({'metadata': {'device_name': 'device_name_0',
                                      'shot_number': <test_shot>}})
results = query.run_query()
print(results)
```

6. Confirm the compound index enforces uniqueness: attempt to archive the same `(shot_number, device_name)` twice — it should raise a `DuplicateKeyError`.

---

## Step 7 — Verify Full Integration

Run one complete experimental cycle with the new instrument active:

1. Set the device in `control.config` (`acqs_to_use` or `acts_to_use`).
2. Start the control loop via `exp_setup.py` as normal.
3. Fire one shot and confirm:
   - The instrument acquired data without errors.
   - The data was archived to `acquisitions` (or `fs.files` for GridFS).
   - If a diagnostic class was added, the result was archived to `processed_data`.
   - The data can be retrieved and visualized via the standard query workflow.
4. Check the log file for any errors or warnings.
5. Confirm no existing instruments were disrupted (check a known-good device for the same shot).

---

## Quick Checklist

- [ ] Instrument class created, inherits `GaladrielInstrument`, implements `acquire`, `adjust`, `archive`
- [ ] `metadata['instrument']` registered in `instruments` collection
- [ ] `metadata['diagnostic']` registered in `diagnostics` collection
- [ ] `data_info` populated for every key in `self.data`
- [ ] Added to `acquisition_init.py` or `actuator_init.py` (Linux/server instruments only)
- [ ] `[device_name]` block added to `control.config`
- [ ] Device added to `acqs_to_use` or `acts_to_use` in `control.config`
- [ ] Diagnostic class created and registered (if applicable)
- [ ] Basic connectivity verified
- [ ] Single-shot archival verified in database
- [ ] Full control loop integration verified

---

## Reference Files

| File | Purpose |
|---|---|
| `galadriel/instruments/windows_insts/wizzler/wizzler.py` | Canonical Windows file-watcher instrument template |
| `galadriel/instruments/interface.py` | Linux `GaladrielInstrument` base class |
| `galadriel/instruments/windows_insts/interface.py` | Windows `GaladrielInstrument` base class |
| `galadriel/control/control_setup/acquisition_init.py` | Where to wire in new acquisition instruments |
| `galadriel/control/control_setup/actuator_init.py` | Where to wire in new actuator instruments |
| `galadriel/control/control_setup/diagnostics_init.py` | Where to wire in new diagnostic classes |
| `galadriel/control/control.config` | Device configuration — connection params, archive tags |
| `MORIA_User_Manual__version_1_0_1.pdf` | Full MORIA schema and API reference |

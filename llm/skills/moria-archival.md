---
name: moria-archival
description: This skill should be used when the user wants to "archive data", "store data to the database", "ingest files", "archive instrument data", "upload data to MORIA", or "add data from [instrument name] to GALADRIEL". Guides the full workflow for translating external data files into the MORIA schema and archiving them into the GALADRIEL database.
version: 1.0.0
---

# MORIA Data Archival Skill

This skill implements the expert archival workflow for ingesting external instrument data files into the MORIA/GALADRIEL MongoDB database. Follow all five steps in order.

## MORIA Schema Quick Reference

See `MORIA_User_Manual__version_1_0_1.pdf` in the working directory for full detail.

### Collections
| Collection | Purpose |
|---|---|
| `acquisitions` | Raw scalar/array data per device per shot |
| `fs.files` / `fs.chunks` | Images or data files >16 MB (GridFS) |
| `processed_data` | Post-processed or diagnostic-level results |
| `diagnostics` | Registry of diagnostic labels (admin) |
| `instruments` | Registry of instrument types + GridFS flag (admin) |
| `run_setup` | Global shot counter and experiment name |

### Required Metadata Fields (acquisitions and fs.files)
- `shot_number` : int — unique per device, from `run_setup.last_shot`
- `experiment` : str — current experiment name from `run_setup`
- `trigger_timestamp` : ISODate — time of acquisition (from file timestamp)
- `archive_timestamp` : ISODate — time of archival (now)
- `instrument` : str — **must exist in `instruments` collection**
- `diagnostic` : str — **must exist in `diagnostics` collection**
- `device_name` : str — unique device identifier (compound index with shot_number)
- `data_info` : dict — one entry per data field: `{data_type, units, description}`
- `notes` : list

### Uniqueness Constraint
The compound index `(metadata.shot_number, metadata.device_name)` is enforced on `acquisitions` and `fs.files`. Attempting to archive a duplicate will raise an error — this is the primary duplicate-prevention mechanism.

### GridFS Rule
If the instrument's data may exceed **16 MB** (images, large arrays), set `gridfs=True` in `instruments`. The data must be stored under the `buffer` key in the data dictionary.

### Naming Convention
Use **UPPERCASE with underscores** for instrument and diagnostic names (e.g., `PHASE_CONTROLLER`, `LASER_ENERGY`). This is not strictly required but is the established convention at GALADRIEL.

---

## Step 1 — Understand the Data Files

Before writing any archival code, gather the following from the user or by reading the files directly:

1. **File format**: What format are the files (HDF5, CSV, binary, TIFF, etc.)?
2. **Fields/channels**: What does each field or channel in the file represent?
3. **Units**: What are the physical units for each data field?
4. **File naming convention**: Does the filename encode timestamp, shot number, or device identity?
5. **Data size**: Is any field likely to exceed 16 MB per shot? (Determines GridFS vs acquisitions)
6. **Device identity**: What is the unique `device_name` for each physical unit? (e.g., for two Mikan oscillators, `mikan_osc_0` and `mikan_osc_1`)

Ask the user for any information that cannot be determined from the file contents alone.

---

## Step 2 — Classify Each Device

For each instrument/device being archived, determine:

| Decision | Action |
|---|---|
| Data is scalar or 1D array, total size < 16 MB | Archive to `acquisitions` |
| Data is an image or > 16 MB | Archive to `fs.files`/`fs.chunks` (GridFS); store under `buffer` key |
| Data is a post-processed result not tied to a single device | Archive to `processed_data` |

Also determine:
- **`instrument`** label: General type classification (e.g., `WIZZLER`, `OSCILLOSCOPE`, `REGEN_AMP`). Check `instruments` collection first.
- **`diagnostic`** label: The physical quantity being measured (e.g., `SPECTRAL_PHASE`, `LASER_ENERGY`, `PULSE_DURATION`). Check `diagnostics` collection first.
- **`device_name`**: Unique identifier for the specific hardware unit (e.g., `wizzler_0`, `mikan_osc_0`).

---

## Step 3 — Determine Shot Association

Shot numbers must be assigned to each file. Use the following approach:

1. Query `run_setup` to get `last_shot` and `experiment` name.
2. Match files to shots by **trigger timestamp**: the file's modification/creation timestamp or an embedded timestamp should correspond to the shot time. Verify against the `run_setup` shot counter cadence if possible.
3. If multiple files share the same shot (different devices firing on the same pulse), they share the same `shot_number` but have different `device_name` values.
4. If the shot mapping is ambiguous, ask the user to clarify before proceeding.

---

## Step 4 — Register Instruments and Diagnostics

Check the database before archiving. If any instrument or diagnostic is missing, add it.

**Check instruments:**
```python
# Query via MCP or MORIA API
db.instruments.find_one({"instrument": "INSTRUMENT_NAME"})
```
If not found, add it:
```python
admin.add_instrument("INSTRUMENT_NAME", gridfs_bool=False)  # or True if GridFS
```

**Check diagnostics:**
```python
db.diagnostics.find_one({"diagnostic": "DIAGNOSTIC_NAME"})
```
If not found, add it:
```python
admin.add_diagnostic("DIAGNOSTIC_NAME")
```

**Provide suggestions**: Before adding new entries, check existing instruments and diagnostics and propose names consistent with the established convention. If the database is empty, follow the naming convention from the manual and the examples in this skill.

---

## Step 5 — Write and Run the Archival Script

Write a Python script using the MORIA API (`StorageAPI.insert_data`). The script must:

1. **Not overwrite existing data**: The compound index enforces this at the DB level, but the script should also catch `DuplicateKeyError` and skip or log the conflicting document rather than crashing.
2. **Archive in bulk**: Loop over all files, build the document dict, and call `insert_data` for each.
3. **Use exact required metadata fields** as listed in Step 1's schema reference.
4. **Populate `data_info`** with a description entry for every key in the `data` dict.

**Script template (acquisitions):**
```python
from database import Database, StorageAPI, AdminAPI
from datetime import datetime, timezone

db = Database("galadriel", server_ip="galadriel.gat.com")
storage = StorageAPI(db)

for shot_number, filepath in shot_file_map.items():
    raw = load_file(filepath)  # user-defined loader

    document = {
        "data": {
            "field_a": raw["field_a"],
            "field_b": raw["field_b"],
        },
        "metadata": {
            "shot_number": shot_number,
            "experiment": "EXPERIMENT_NAME",
            "trigger_timestamp": raw["timestamp"],        # ISODate
            "archive_timestamp": datetime.now(timezone.utc),
            "instrument": "INSTRUMENT_NAME",
            "diagnostic": "DIAGNOSTIC_NAME",
            "device_name": "device_0",
            "data_info": {
                "field_a": {"data_type": "float", "units": "fs", "description": "..."},
                "field_b": {"data_type": "array[float]", "units": "nm", "description": "..."},
            },
            "notes": [],
        },
    }

    try:
        storage.insert_data(document)
    except Exception as e:
        if "duplicate" in str(e).lower():
            print(f"Shot {shot_number} already archived for device_0 — skipping.")
        else:
            raise
```

**For GridFS (images/large data):**
```python
import io
document["data"]["buffer"] = image_bytes  # bytes object, not the raw array
```

---

## Anomaly Handling

Handle each anomaly on a case-by-case basis:
- **Missing timestamp in file**: Fall back to file system `mtime`; add a note in the document's `notes` list.
- **Shot number gap**: Log and confirm with user before skipping.
- **File read error**: Log the filename and continue; report all failures at the end.
- **Ambiguous device_name**: Ask the user to confirm the mapping before bulk archival.

---

## Reference

Full schema details, API signatures, and examples: `MORIA_User_Manual__version_1_0_1.pdf` (working directory), especially:
- Section 6.1 — Tables and Fields (required fields per collection)
- Section 6.2.4 — Storage API (`insert_data`)
- Section 6.2.1 — Administration API (`add_instrument`, `add_diagnostic`)

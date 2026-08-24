### Getting Started

Run the scripts in the following order. **Note:** Later scripts assume that earlier ones have already populated the database.

1. **Create the Database:** Run `database_utils/create_database '<db_name>'` (assumes MongoDB is set up and running on your target server).
2. **Configure the Path:** Modify the `moria_path`, `db_name`, and `server_ip` variables in `connection.py` to match your setup.
3. **Initialize Admin Data:** Run `admin_examples.py` to add two instruments and one diagnostic to the database.
4. **Archive Data:** Run `storage_examples.py` to archive simulated data and images corresponding to the devices set up in the previous step.
5. **Run Queries:** Execute `query_examples.py` to perform three simulated queries on the archived data.
6. **Test Updates:** Run `update_examples.py` (you can uncomment specific operations in the file to test them).
7. **Experiment:** Feel free to modify the scripts and play around with different setups!

### File Reference

| File | Description |
| :--- | :--- |
| `connection.py` | Shared database connection imported by every other script |
| `admin_examples.py` | Registering the experiment, instruments, and diagnostics |
| `storage_examples.py` | Archiving scalar data, image/GridFS data, per-shot processed data, and batch-level averages |
| `query_examples.py` | Single value queries, range queries with related-data fetches, and combined value/range queries |
| `update_examples.py` | Update commands (`replace`, `insert`, `append`) and the `add_note_to_doc()` convenience method |

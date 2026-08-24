This file will ultimately explain the design for which pieces of information should live as context vs reuable skill files, along with perhaps explaining some best practices for deploying context (documents here vs say available via RAG).

Notes from 8/24 meeting:

1) Data Storage/organization understanding should be its own skill/context (used in archival, add instrument, and remediate_data skills)
2) Control System operation/organization should be an additional skill/context (used mainly when adding instruments, maybe when trying to interpret data remediation issues/problems)

Known context which should exist:
- Files (markdown?) explaining the data systems which exist for a given facility - What all data storage systems exist?
- Known information about a particular instantiation of a data archival design (ie. how does facility X store data across various systems) - How is the data organized across the various systems?
- Metadata about the facility's data (effectively cached query results or results of scans, source of truth) - What data has been collected and where?

Once we have dialed in the archival skill/structure we can move on to instrument adding/upload. Until we talk to scott, the main thing we will do for said skillfile is move all the examples/referenced files outside of the skillfile itself (keep it short), breaking out some of the reusable capabilities like "check for diagnostic/instrument", then we can review with him the overall structure at some juncture (maybe wednesday?). The skill in its current form plus these quality of life changes should be enough for RJ to try adding the thermocouples.

Initial prompts defining the two needs (LLM benchmarks):

Prompt 1 (external data archival):
"I have data from three instruments: the Wizzler, the Mikan (oscillator), and the Regen (regenerative amplifier), all from Fastlite. The data is located in the following directory: <your local directory>, I would like you to archive these files to the MORIA galadriel database.

Prompt 2 (device integration, Scott's task):
"Write two simple class files to archive the oscillator and regenerative amplifier (Regen) data during future experimental runs. The data is stored on an external laptop alongside the Wizzler data at <spectral file paths>. The classes should follow the same general structure and functionality as the existing Wizzler class."

Remaining email context (basis for existing llm/skills)

Here is what I would do as the expert given Task 1:
1. Request information about the data file structure, including what each field represents.
2. Determine what data is needed based on the user’s request. Identify what should be stored as metadata, what constitutes the acquired (raw) data, and whether the data should be stored in GridFS.
3. Determine which shot the data should be associated with, likely based on the file timestamps.
4. Determine whether the instruments/diagnostics and associated database entries already exist. If not, add them to the appropriate collections based on the schema documentation.
- I would provide suggestions based on similar instruments or diagnostics that have already been archived. If the database is empty, I would follow the schema documentation.
5. Write a simple storage script to archive the data in bulk.
- The script should ensure that duplicate shots are not written for the same device and that existing data cannot be overwritten.
- I would handle any anomalies on a case-by-case basis.

Here is what I would do as the expert given Task 2:
1. Create an instrument class based on similar existing classes and the user’s requirements.
2. Add the new class to one of the experimental initialization files based on its function (acquisition or actuator). Register it in the instruments collection, if not already there.
3. Create an associated diagnostic class if needed. Register it in the diagnostic initialization and diagnostic collection, if not already there.
4. Add them to control.config.
5. Verify basic connectivity.
6. Verify that commands can be sent to the instrument and that data can be retrieved from it.
7. Verify that archiving and the automated analysis works correctly and that the data can be viewed in the database.

# BIDS2NDA
Extract [NIMH Data Archive](https://nda.nih.gov/) compatible metadata from [Brain Imaging Data Structure (BIDS)](https://bids-specification.readthedocs.io/) compatible datasets.

This builds a [`image03.csv`](https://nda.nih.gov/data-structure/image03) data structure for upload with [nda-tools](https://github.com/NDAR/nda-tools) or [web uploader](https://nda.nih.gov/vt/).
Data must first be organized in BIDS (see [bids-validator](https://bids-validator.readthedocs.io/en/stable/)) and [NDA's Global Unique IDentifiers](https://nda.nih.gov/nda/data-standards#guid) must have already been generated.

## Installation


    pip install https://github.com/INCF/BIDS2NDA/archive/master.zip


## Usage

    usage: bids2nda [-h] [-v] BIDS_DIRECTORY GUID_MAPPING OUTPUT_DIRECTORY

    BIDS to NDA converter.

    positional arguments:
      BIDS_DIRECTORY    Location of the root of your BIDS compatible directory.
      GUID_MAPPING      Path to a text file with participant_id to GUID mapping.
                        You will need to use the GUID Tool
                        (https://ndar.nih.gov/contribute.html) to generate GUIDs
                        for your participants.
      OUTPUT_DIRECTORY  Directory where NDA files will be stored.

    optional arguments:
      -h, --help        Show this help message and exit.

## Prerequisites

Here is an example directory tree. In addition to BIDS organized `.nii.gz` and `.json` files, you will also need a GUID mapping, participants, and scans file.
```
guid_map.txt # ** GUID_MAPPING file: id lookup
BIDS/
├── participants.tsv # ** Participants File: age, sex
└── sub-10000
    └── ses-1
        ├── anat
        │   ├── sub-10000_ses-1_T1w.json
        │   ├── sub-10000_ses-1_T1w.nii.gz
        ├── func
        │   ├── sub-10000_ses-1_task-rest_bold.json
        │   ├── sub-10000_ses-1_task-rest_bold.nii.gz
        └── sub-10000_ses-1_scans.tsv # ** Scans File: acq_time->interview_date
```


### GUID_MAPPING file format
The is the file format produced by the [GUID Tool](https://nda.nih.gov/nda/nda-tools#guid-tool), one line per subject in the format:

`<participant_id> - <GUID>`

It is not part of the BIDS specification.
The file translates BIDS subject id into NDA participant id (GUID) and can be stored anywhere.
Its location is explicitly given to the `bids2nda` command.

### Participants File
A [Participants File](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#participants-file) is at the BIDS root like `BIDS/participants.tsv`.
It should at least have columns `participant_id`, `age`, and `sex`.

|col|desc|notes|
|---|---|---|
|`particiapnt_id` | like `sub-X` | does not include session label (See [Sessions File](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#sessions-file). Not supported here) |
|`age` | number in years | converted to months for NDA's `interview_age`|
|`sex` |||

Contents could look like
```
participant_id	sex	age
sub-100000  	M	46
```

### Scans File

[Scans File](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#scans-file) is at the session (or subject if session is omitted) level like `BIDS/sub-X/ses-1/sub-X_ses-1_scans.tsv`. 
It must have at least `filename` and `acq_time`.

|col|desc|notes|
|---|---|---|
|`filename`| like `func/sub-X_bold.nii.gz` | relative to session root |
|`acq_time`| date like `YYYY-MM-DD` | creates `interview_date` NDA column|


Contents could look like
```
acq_time	filename
2000-12-31	anat/sub-100000_ses-1_T1w.nii.gz
2000-12-31	func/sub-100000_ses-1_task-rest_bold.nii.gz
```

## Example outputs
See [/examples](/examples)

## Notes:
Column `'experiment_id'` must be manually filled.
For `_bold` suffixes, the value stored in the json sidecar with the key `ExperimentID` will be used.
This is based on experiment IDs received from NDA after setting the study up through the NDA website [here](https://ndar.nih.gov/user/dashboard/collections.html).

---

## Real Life Example from April 2026: NDA Neuroimaging Upload Workflow

### Tools needed

- **bids2nda** — converts BIDS directory to `image03.csv` and also includes `make_scans_tsv` (see below)
- **nda-tools (vtcmd)** — validates and uploads to NDA
- **pydicom** — extracts scan dates from DICOM headers (installed automatically with bids2nda)
- **make_scans_tsv** — generates `scans.tsv` per session from a DICOM file; bundled inside bids2nda, available as a command after installation

### Installation

It is recommended to create a virtual environment first:

```bash
python3 -m venv ./nda-env
source ./nda-env/bin/activate
```

Then install:

```bash
pip install git+https://github.com/argyelan/bids2nda.git
pip install nda-tools
```

---

### Step 1 — Create a separate BIDS directory for upload

Before running on your full dataset, test with a single subject.

```bash
mkdir -p ./test_bids

# copy one subject folder
cp -r /data/BIDS/sub-1XXXX ./test_bids/

# copy required BIDS metadata files
cp /data/BIDS/dataset_description.json ./test_bids/
cp /data/BIDS/participants.tsv ./test_bids/

# trim participants.tsv to only that subject (keep header + one line)
head -1 /data/BIDS/participants.tsv > ./test_bids/participants.tsv
grep "1XXXX" /data/BIDS/participants.tsv >> ./test_bids/participants.tsv
```

---

### Step 2 — Prepare guids.txt

The format must be exactly:

```
1XXXX - NDAR_INV1A2B3C4D
1YYYY - NDAR_INV5E6F7G8H
```

Rules:
- No `sub-` prefix on subject IDs
- Separator must be ` - ` (space-dash-space)
- One subject per line, no blank lines

Generate GUIDs via the [NDA GUID Tool](https://nda.nih.gov/tools/nda-tools.html).

---

### Step 3 — Generate scans.tsv for each session

Each session folder needs a `sub-XX_ses-YY_scans.tsv` file with scan dates. Use the `make_scans_tsv` command (bundled with bids2nda) with any DICOM file from that session:

```bash
make_scans_tsv \
    --dicom /path/to/dicom/file.dcm \
    --session ./test_bids/sub-1XXXX/ses-2XXXX
```

This reads the acquisition date from the DICOM header and writes `sub-1XXXX_ses-2XXXX_scans.tsv` directly into the session folder.

Repeat for every session of every subject before running `bids2nda`. If you have many sessions, it is recommended to script this step.

---

### Step 4 — Fix non-standard BIDS suffixes

`bids2nda` only recognises standard BIDS suffixes. First check what suffixes you have:

```bash
find ./test_bids/ -name "*.nii.gz" | sed 's/.*_//' | sed 's/\.nii\.gz//' | sort -u
```

If a suffix is not required by NDA (e.g. `spec`, `neuromelanin`), simply remove those files from the temporary BIDS directory — this is the recommended approach.

---

### Step 5 — Run bids2nda

```bash
mkdir -p ./test_output
bids2nda ./test_bids/ guids.txt ./test_output
```

If successful you will see: `Metadata extraction complete.`

Output in `./test_output/`:
- `image03.csv` — one row per scan per subject
- `*.metadata.zip` — BIDS JSON sidecars per scan, referenced in `image03.csv`

**Manual edits needed in image03.csv:**
- Remove fMRI rows you do not want to upload
- Fill in `experiment_id` for each fMRI row — this is collection-specific and must be obtained from NDA
- Verify that `interview_age` matches what is in `ndar_subject01.csv` (discrepancies can occur because `image03.csv` derives age from the DICOM date, while `ndar_subject01.csv` may use enrollment age)
- Make sure `src_subject_id` matches `ndar_subject01.csv` — it must be the internal subject ID, not the GUID

---

### Step 6 — Prepare ndar_subject01.csv

Download the blank template from: https://nda.nih.gov/data_structure?short_name=ndar_subject01

Required fields:

| Field | Description |
|---|---|
| `subjectkey` | GUID (e.g. `NDAR_INV1A2B3C4D`) |
| `src_subject_id` | your internal subject ID |
| `interview_date` | date of scan (MM/DD/YYYY) |
| `interview_age` | age in months at time of scan |
| `sex` | M or F |
| `race` | NDA controlled vocabulary |
| `ethnic_group` | NDA controlled vocabulary |

> **Note:** `siblings_living_together` is a mandatory field — do not forget to fill it in (e.g. `No`).

---

### Step 7 — Validate and upload with vtcmd

```bash
vtcmd ./test_output/image03.csv ndar_subject01.csv \
      -m ./test_output \
      -w \
      -c <collection_id> \
      -t "Submission title" \
      -d "Submission description" \
      -u <username>
```

Key flags:

| Flag | Description |
|---|---|
| `-c` | Numeric collection ID only — no `C` prefix (e.g. `5824` not `C5824`) |
| `-m` | Directory containing the `.metadata.zip` files |
| `-w` | Enables actual upload to AWS after validation |
| `-b` | Batch mode — triggers the final upload; add this once validation passes |

This first run (without `-b`) only validates. Once validation passes, add `-b` to trigger the final upload:

```bash
vtcmd ./test_output/image03.csv ./test_output/ndar_subject01.csv \
      -m ./ -w -c <collection_id> \
      -t "Cinema first submission" \
      -d "These are the first two patients" \
      -u <NDA username> -b
```

---

### Common Gotchas

| Problem | Fix |
|---|---|
| `KeyError` on subject ID in guids.txt | Use bare numeric ID, no `sub-` prefix; separator must be ` - ` |
| `scans.tsv` file not found | Run `make_scans_tsv` for each session first |
| `KeyError` on suffix (e.g. `spec`) | Delete those files/folders from the temporary BIDS directory |
| `FileNotFoundError` on output zip | Installing from `argyelan/bids2nda` handles this automatically via absolute paths |
| `invalid positive_int value: 'C5824'` | Drop the `C`, use just `5824` |
| Windows line endings in guids.txt | Fix with `sed -i 's/\r//' guids.txt` |
| `experiment_id` missing | Must be filled in manually for each fMRI scan |
| Age mismatch | `interview_age` in `image03.csv` must match `ndar_subject01.csv` |
| Subject ID mismatch | `src_subject_id` must match `ndar_subject01.csv` (not the GUID) |

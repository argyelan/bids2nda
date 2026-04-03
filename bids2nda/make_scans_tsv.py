#!/usr/bin/env python3
"""
Generate a BIDS scans.tsv file for a session using a DICOM file for date/time info.

Usage:
    python make_scans_tsv.py --dicom /path/to/file.dcm --session /path/to/bids/sub-XX/ses-YY
"""

import os
import argparse
import pydicom
from datetime import datetime
from pathlib import Path


def get_acq_time(dicom_path):
    dcm = pydicom.dcmread(dicom_path, stop_before_pixels=True)

    date = getattr(dcm, 'StudyDate', None) or getattr(dcm, 'AcquisitionDate', None)
    time = getattr(dcm, 'StudyTime', None) or getattr(dcm, 'AcquisitionTime', None)

    if not date or not time:
        raise ValueError(f"Could not find date/time in DICOM header: {dicom_path}")

    time = time.split('.')[0].ljust(6, '0')  # ensure HHMMSS format
    acq_time = datetime.strptime(date + time, '%Y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
    return acq_time


def find_niftis(session_dir):
    """Find all NIfTI files in the session directory, return relative paths."""
    session_path = Path(session_dir)
    niftis = sorted(session_path.rglob('*.nii.gz'))
    # return paths relative to the session directory
    return [str(f.relative_to(session_path)) for f in niftis]


def make_scans_tsv(dicom_path, session_dir):
    acq_time = get_acq_time(dicom_path)
    niftis = find_niftis(session_dir)

    if not niftis:
        raise ValueError(f"No .nii.gz files found in {session_dir}")

    # determine output path
    session_path = Path(session_dir)
    # extract sub and ses from folder names
    parts = session_path.parts
    sub = next((p for p in parts if p.startswith('sub-')), None)
    ses = next((p for p in parts if p.startswith('ses-')), None)

    if sub and ses:
        tsv_name = f"{sub}_{ses}_scans.tsv"
    else:
        tsv_name = "scans.tsv"

    output_path = session_path / tsv_name

    with open(output_path, 'w') as f:
        f.write("filename\tacq_time\n")
        for nifti in niftis:
            f.write(f"{nifti}\t{acq_time}\n")

    print(f"Written: {output_path}")
    print(f"  acq_time: {acq_time}")
    print(f"  {len(niftis)} NIfTI files included:")
    for n in niftis:
        print(f"    {n}")


def main():
    parser = argparse.ArgumentParser(description="Generate BIDS scans.tsv from a DICOM file.")
    parser.add_argument('--dicom', required=True, help='Path to a DICOM file from the session')
    parser.add_argument('--session', required=True, help='Path to the BIDS session directory (e.g. /data/BIDS/sub-14961/ses-24496)')
    args = parser.parse_args()

    make_scans_tsv(args.dicom, args.session)


if __name__ == "__main__":
    main()

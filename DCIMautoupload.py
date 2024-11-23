#!/usr/bin/env python3

import os, sys, glob
import argparse
import itertools

import pyexiv2 # apt install python3-py3exiv2
from rclone_python import rclone # pip install rclone-python

EXTENSIONS = [".JPG", ".RW2", ".ORF", ".ARW", ".DNF"] # TODO: from config
REMOTE = "sciebo:DCIM/" # TODO: from config

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("event", help="event (as passed from udiskie)", type=str)
    parser.add_argument("mount_path", help="mount_path (as passed from udiskie)", type=str, nargs='?', default="")
    args = parser.parse_args()

    if args.event != "device_mounted":
        print("different event than 'device_mounted', exiting...")
        exit(1)

    DCIM = os.path.join(args.mount_path, "DCIM")
    if not os.path.isdir(DCIM):
        print(f"no DCIM folder in {args.mount_path}, exiting...")
        exit(1)

    files = [glob.glob(os.path.join(DCIM, "**", f"*{ext}")) for ext in EXTENSIONS]
    files = list(itertools.chain(*files))

    print(f"DCIM auto uploader working on {DCIM} with {len(files)} files :)")

    for file_path in files:
        try:
            folder, file = os.path.split(file_path)
            base, ext = os.path.splitext(file)
            ext = ext.lstrip('.').lower()
            
            exif = pyexiv2.ImageMetadata(file_path)
            exif.read()
            model = exif["Exif.Image.Model"].value.strip()
            dt = exif["Exif.Image.DateTime"].value
            
        except Exception as e:
            print("Error handling", file, e)
            continue

        newname = f"{dt.strftime('%Y%m%d_%H%M%S')}_{model}_{base}.{ext}"
        #print(file, "→", newname)
        try:
            rclone.copyto(file_path, REMOTE+newname, ignore_existing=True, show_progress=False, args=[])
        except KeyError as ke:
            print(f"KeyError on {file}:", ke)
        except rclone.RcloneException as rce:
            print(f"rclone fail on {file}:", rce)
        else:
            print(f"Upload success {file} → {newname}")
        sys.stdout.flush()

    # os.system(f"udiskie-umount {args.mount_path}")
    print(f"DCIM auto uploader done with {DCIM} :)")

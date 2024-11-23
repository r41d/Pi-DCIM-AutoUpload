#!/usr/bin/env python3

import os, glob
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

    files = [glob.glob(os.path.join(DCIM, "**", f"*{ext}")) for ext in EXTENSIONS]
    files = list(itertools.chain(*files))

    print(f"DCIM auto uploader called for folder {DCIM} with {len(files)} files :)")

    for file_path in files:
        try:
            folder, file = os.path.split(file_path)
            base, ext = os.path.splitext(file)
            ext = ext.lstrip('.').lower()
            
            exif = pyexiv2.ImageMetadata(file_path)
            exif.read()
            model = exif["Exif.Image.Model"].value
            dt = exif["Exif.Image.DateTime"].value
            
        except Exception as e:
            print("Error handling", file, e)
            continue

        newname = f"{dt.strftime('%Y%m%d_%H%M%S')}_{model}_{base}.{ext}"
        # print(file, "→", newname)
        rclone.copyto(file_path, REMOTE+newname, ignore_existing=True, args=[])

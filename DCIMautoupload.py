#!/usr/bin/env python3

import os, sys, glob
import hashlib
import datetime
import argparse
import itertools

import zoneinfo # pip install tzdata
import pyexiv2 # apt install python3-py3exiv2
import exiftool # pip install PyExifTool / apt install exiftool
from rclone_python import rclone # pip install rclone-python
from rclone_python.hash_types import HashTypes

EXTENSIONS = [
    "JPG", "JPEG", "TIF", "TIFF", "HIF", "HEIF", "HEIC", # non-raw pictures
    "XMP", # metadata
    "DNG", "RAW", # "universal" raw extensions
    "CRW", "CR2", "CR3", # Canon
    "RAW", # Fujifilm
    "3FR", "FFF", # Hasselblad
    "DCR", "DCS", "KDC", # Kodak
    "RWL", # Leica
    "MRW", "MDC", # Minolta
    "NEF", "NRW", # Nikon
    "ORF", "ORI", # Olympus
    "RW2", # Panasonic
    "PEF", # Pentax
    "SRW", # Samsung
    "X3F", # Sigma
    "ARW", "SRF", "SR2", # Sony
]
# TODO: from config
REMOTE_NAME = "sciebo"
REMOTE_DIR = "DCIM"


class Uploader:
    def __init__(self, REMOTE_NAME, REMOTE_DIR):
        if not rclone.check_remote_existing(REMOTE_NAME):
            print(f"rclone remote {REMOTE_NAME} does not exist, exiting...")
            exit(1)
        self.REMOTE = f"{REMOTE_NAME}:{REMOTE_DIR}"
        self.sha1remote = rclone.hash(HashTypes.sha1, self.REMOTE)

    @staticmethod
    def base_ext(file_path):
        folder, file = os.path.split(file_path)
        base, ext = os.path.splitext(file)
        ext = ext.lstrip('.').lower()
        return base, ext

    @staticmethod
    def sha1sum(file_path):
        with open(file_path, 'rb', buffering=0) as f:
            return hashlib.file_digest(f, 'sha1').hexdigest()

    def is_file_hash_present(self, file_path):
        return self.sha1sum(file_path) in self.sha1remote.values()

    def upload(self, src, dst):
        try:
            rclone.copyto(src, os.path.join(self.REMOTE, dst), ignore_existing=True, show_progress=False, args=[])
        except KeyError as ke:
            print(f"KeyError on {src}:", ke)
        except rclone.RcloneException as rce:
            print(f"rclone fail on {src}:", rce)
        else:
            print(f"Upload success {src} → {dst}")
        sys.stdout.flush()


def uploadDCIM(mount_path, uploader):
    DCIM = os.path.join(args.mount_path, "DCIM")
    if not os.path.isdir(DCIM):
        print(f"no DCIM folder in {args.mount_path}, exiting...")
        exit(1)

    extensions = EXTENSIONS + list(map(str.lower, EXTENSIONS)) # consider both upper and lower case
    files = [glob.glob(os.path.join(DCIM, "**", f"*.{ext}")) for ext in extensions]
    files = sorted(itertools.chain(*files))

    print(f"DCIM auto uploader working on DCIM path {DCIM} for {len(files)} files :)")

    for file_path in files:

        if uploader.is_file_hash_present(file_path): # check before expensive computations on file
            print(f"hash for {file_path} already present on remote, skipping...")
            continue

        try:
            exif = pyexiv2.ImageMetadata(file_path)
            exif.read()
            model = exif["Exif.Image.Model"].value.strip()
            dt = exif["Exif.Image.DateTime"].value

        except Exception as e:
            print("Error handling", file_path, e)
            continue

        base, ext = uploader.base_ext(file_path)
        newname = f"{dt.strftime('%Y%m%d_%H%M%S')}_{model}_{base}.{ext}"
        uploader.upload(file_path, newname)


def uploadMP4(mount_path, uploader):

    MP4 = os.path.join(mount_path, "PRIVATE", "M4ROOT", "CLIP")
    if not os.path.isdir(MP4):
        print(f"no M4ROOT found, no mp4 upload...")
        return

    files = [glob.glob(os.path.join(MP4, f"*.{ext}")) for ext in ["MP4"]]
    files = sorted(itertools.chain(*files))
    print(f"DCIM auto uploader working on MP4 path {MP4} for {len(files)} files...")

    for file_path in files:

        if uploader.is_file_hash_present(file_path): # check before expensive computations on file
            print(f"hash for {file_path} already present on remote, skipping...")
            continue

        with exiftool.ExifToolHelper() as et:
            meta = et.get_metadata(file_path)[0]
            try:
                date = meta["XML:CreationDateValue"]
                dt = datetime.datetime.strptime(date, "%Y:%m:%d %H:%M:%S%z")
                print(f"using date from XML:CreationDateValue for {file_path}")
            except:
                try: # fallback 1
                    date = meta["QuickTime:CreateDate"]
                    dt = datetime.datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
                    dt = dt.astimezone(zoneinfo.ZoneInfo("Europe/Berlin")) # man darf nur hoffen dass das für Sommerzeit tut
                    print(f"using date from QuickTime:CreateDate for {file_path}")
                except: # fallback 2
                    date = meta["File:FileModifyDate"] # das sollte es eigentlich immer geben
                    dt = datetime.datetime.strptime(date, "%Y:%m:%d %H:%M:%S%z")
                    print(f"using date from File:FileModifyDate for {file_path}")

            try:
                model = meta["XML:DeviceModelName"]
            except: # fallback
                print(f"could not determine model for {file_path} :(")
                model = "UNKNOWN"

        base, ext = uploader.base_ext(file_path)
        newname = f"{dt.strftime('%Y%m%d_%H%M%S')}_{model}_{base}.{ext}"
        uploader.upload(file_path, newname)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("event", help="event (as passed from udiskie)", type=str)
    parser.add_argument("mount_path", help="mount_path (as passed from udiskie)", type=str, nargs='?', default="")
    args = parser.parse_args()

    if args.event != "device_mounted":
        print("different event than 'device_mounted', exiting...")
        exit(1)

    uploader = Uploader(REMOTE_NAME, REMOTE_DIR)

    uploadDCIM(args.mount_path, uploader)

    uploadMP4(args.mount_path, uploader)

    # maybe implement AVCHD later...
    #MTS = os.path.join(args.mount_path, "PRIVATE", "AVCHD", "BDMV", "STREAM")

    # os.system(f"udiskie-umount {args.mount_path}")
    print(f"DCIM auto uploader done with {args.mount_path} :)")

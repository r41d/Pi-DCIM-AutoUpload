# Pi DCIM AutoUpload
Pi DCIM AutoUpload automatically uploads contents of DCIM folders from arbitrary USB storage devices.

In contrast to the majority of other approaches that I found online it does NOT hardcode mount paths or devices, udiskie is utilized for automatically mounting arbitrary SD cards / USB sticks.
The majority of sources that I found recommended using `/etc/fstab`, which means hardcoding device paths / UUIDs and mount paths, which is NOT what I wanted, since it should work with arbitrary devices/cameras.
Also, the package `usbmount` was mentioned often, but this seems to be unmainted for many years and was also removed from the Debian package respository many years ago, hence it's not an option.

This tool is intended for Raspbian Lite installations since those don't include an automounter.

# Installation
Copy the project folder to the pi and run `sudo ./install.sh`

Next, configure rclone, I use sciebo for that and a folder named `DCIM`, but that's up to you.
You may need to adapt the `REMOTE` variable in the script.

# Usage
Plug camera via USB cable (or SD card in SD card reader) into the pi and wait :)

Progress can be seen with `journalctl -fu DCIMautoupload.service` or in the remote destination.

# Notes/Problems

## consolekit.pkla
On the [official guide](https://github.com/coldfix/udiskie/wiki/Ubuntu-Debian-installation-guide) one line reads `Action=org.freedesktop.udisks.*` but I found that it needs a 2 behind udisks to work.

## udiskie.service
udiskie has renamed `--notify-command` to `--event-hook` in January of 2024, introducing a breaking change.
We stick with the version the Raspbian repos gives us for now, which might become newer than a version from 2022 in the future, which will break the current .service file and would then require updating.

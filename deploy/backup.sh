#!/bin/sh
set -eu
umask 077
estate_stamp=$(date -u +%Y%m%dT%H%M%SZ)
estate_backup_dir="/var/backups/estate-os/$estate_stamp"
mkdir -p "$estate_backup_dir"
runuser -u estateos -- pg_dump -h /var/run/postgresql -U estateos -Fc estateos > "$estate_backup_dir/database.dump"
tar -czf "$estate_backup_dir/media.tar.gz" -C /srv/estate-os/shared media
cp /etc/estate-os/production.env "$estate_backup_dir/production.env"
readlink -f /srv/estate-os/current > "$estate_backup_dir/release.txt"
printf 'Estate OS backup complete: %s\n' "$estate_backup_dir"

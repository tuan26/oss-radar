#!/bin/sh
# Thư mục data gắn từ máy host thường thuộc root: sửa quyền rồi chạy app bằng user thường (uid 1000).
set -e
mkdir -p "$DATA_DIR"
if [ "$(id -u)" = "0" ]; then
  chown -R 1000:1000 "$DATA_DIR"
  exec setpriv --reuid=1000 --regid=1000 --init-groups "$@"
fi
exec "$@"

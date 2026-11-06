#!/usr/bin/env bash
# Cài OSS Radar lên VPS Ubuntu/Debian (Vultr, DigitalOcean, ...). Chạy bằng root:
#   curl -fsSL https://raw.githubusercontent.com/tuan26/oss-radar/main/deploy/vultr-setup.sh | bash
# Có tên miền (đã trỏ bản ghi A về IP server) để có HTTPS:
#   curl -fsSL https://raw.githubusercontent.com/tuan26/oss-radar/main/deploy/vultr-setup.sh | DOMAIN=radar.ten-mien.vn bash
# Chạy lại script = cập nhật lên code mới nhất (giữ nguyên dữ liệu và mật khẩu).
set -euo pipefail

REPO="${REPO:-https://github.com/tuan26/oss-radar}"
DIR="${DIR:-/opt/oss-radar}"
DOMAIN="${DOMAIN:-}"

[ "$(id -u)" = "0" ] || { echo "Hãy chạy bằng root (sudo -i rồi chạy lại)."; exit 1; }
export DEBIAN_FRONTEND=noninteractive

echo "==> Cài gói cần thiết"
apt-get update -qq
apt-get install -y -qq git curl ca-certificates ufw openssl >/dev/null

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Cài Docker"
  curl -fsSL https://get.docker.com | sh >/dev/null
fi
systemctl enable --now docker >/dev/null

# Máy 1 GB RAM: thêm 1 GB swap để build image không bị thiếu bộ nhớ
if [ "$(swapon --show | wc -l)" = "0" ] && [ ! -f /swapfile ]; then
  echo "==> Tạo swap 1 GB"
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

echo "==> Lấy code vào $DIR"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --ff-only
else
  git clone --depth 1 "$REPO" "$DIR"
fi
cd "$DIR"
mkdir -p data

# Tệp .env: giữ mật khẩu cũ nếu đã có
touch .env && chmod 600 .env
if ! grep -q '^APP_PASSWORD=.' .env; then
  sed -i '/^APP_PASSWORD=/d' .env
  echo "APP_PASSWORD=$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-20)" >> .env
fi
if [ -n "$DOMAIN" ]; then
  sed -i '/^DOMAIN=/d' .env; echo "DOMAIN=$DOMAIN" >> .env
fi
DOMAIN="$(grep '^DOMAIN=' .env | cut -d= -f2- || true)"

IP="$(curl -fsS --max-time 5 http://169.254.169.254/v1/interfaces/0/ipv4/address 2>/dev/null \
      || curl -fsS --max-time 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
if [ -n "$DOMAIN" ]; then
  URL="https://$DOMAIN"; OVERRIDE="deploy/compose.domain.yml"
else
  URL="http://$IP"; OVERRIDE="deploy/compose.ip.yml"
fi
sed -i '/^APP_URL=/d' .env; echo "APP_URL=$URL" >> .env

echo "==> Mở tường lửa: SSH, HTTP, HTTPS"
ufw allow OpenSSH >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null

echo "==> Build và chạy (lần đầu mất vài phút)"
docker compose -f docker-compose.yml -f "$OVERRIDE" up -d --build --remove-orphans

PASS="$(grep '^APP_PASSWORD=' .env | cut -d= -f2-)"
echo
echo "============================================================"
echo " OSS Radar đã chạy:  $URL"
echo " Đăng nhập: tên gì cũng được, mật khẩu: $PASS"
echo " (mật khẩu lưu trong $DIR/.env — đổi xong chạy lại script)"
[ -z "$DOMAIN" ] && echo " Lưu ý: chưa có HTTPS. Nên trỏ tên miền về $IP rồi chạy lại với DOMAIN=..."
echo " Cập nhật code mới: chạy lại đúng lệnh cài đặt."
echo " Xem log: cd $DIR && docker compose -f docker-compose.yml -f $OVERRIDE logs -f"
echo "============================================================"

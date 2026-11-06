#!/usr/bin/env bash
# Cài OSS Radar lên VPS Ubuntu/Debian (Vultr, DigitalOcean, ...). Chạy bằng root:
#   curl -fsSL https://raw.githubusercontent.com/tuan26/oss-radar/main/deploy/vultr-setup.sh | bash
# Có tên miền (đã trỏ bản ghi A về IP server) để có HTTPS:
#   curl -fsSL https://raw.githubusercontent.com/tuan26/oss-radar/main/deploy/vultr-setup.sh | DOMAIN=radar.ten-mien.vn bash
# Server đang chạy dịch vụ khác (vd tool trading, nginx dùng cổng 80): chọn cổng riêng, không cần tên miền:
#   curl -fsSL .../vultr-setup.sh | APP_PORT=8090 bash
# Xem trước, không thay đổi gì:  ... | CHECK_ONLY=1 bash
# Chạy lại script = cập nhật lên code mới nhất (giữ nguyên dữ liệu và mật khẩu).
#
# AN TOÀN CHO SERVER ĐANG CÓ DỊCH VỤ KHÁC:
#  - KHÔNG bật/tắt tường lửa; chỉ thêm luật mở cổng nếu ufw đã bật sẵn.
#  - KHÔNG cài lại/khởi động lại Docker nếu đã có.
#  - KHÔNG nâng cấp gói hệ thống đã cài; chỉ cài gói còn thiếu.
#  - Kiểm tra cổng trước: cổng đã có chương trình khác dùng thì DỪNG, không làm gì.
#  - Chỉ quản lý container của dự án "oss-radar"; không đụng container khác.
set -euo pipefail

REPO="${REPO:-https://github.com/tuan26/oss-radar}"
DIR="${DIR:-/opt/oss-radar}"
DOMAIN="${DOMAIN:-}"
APP_PORT_SET="${APP_PORT:-}"
APP_PORT="${APP_PORT:-80}"
APP_LOCAL_PORT="${APP_LOCAL_PORT:-}"
PROJECT="oss-radar"

[ "$(id -u)" = "0" ] || { echo "Hãy chạy bằng root (sudo -i rồi chạy lại)."; exit 1; }
export DEBIAN_FRONTEND=noninteractive

# Cổng cần dùng phải còn trống (bỏ qua nếu chính OSS Radar đang giữ cổng đó)
# Lấy DOMAIN/APP_PORT đã lưu từ lần cài trước (nếu có)
if [ -f "$DIR/.env" ]; then
  [ -n "$DOMAIN" ] || DOMAIN="$(grep '^DOMAIN=' "$DIR/.env" | cut -d= -f2- || true)"
  [ "${APP_PORT_SET:-}" ] || APP_PORT="$(grep '^APP_PORT=' "$DIR/.env" | cut -d= -f2- || echo "$APP_PORT")"
  [ -n "$APP_LOCAL_PORT" ] || APP_LOCAL_PORT="$(grep '^APP_LOCAL_PORT=' "$DIR/.env" | cut -d= -f2- || true)"
fi
APP_LOCAL_PORT="${APP_LOCAL_PORT:-8080}"
if [ -n "$DOMAIN" ]; then PORTS="80 443"; else PORTS="$APP_PORT"; fi
OURS=""
command -v docker >/dev/null 2>&1 && OURS="$(docker ps --filter "label=com.docker.compose.project=$PROJECT" -q 2>/dev/null || true)"
command -v ss >/dev/null 2>&1 || { echo "!! Thiếu lệnh 'ss' để kiểm tra cổng. Cài trước: apt-get install -y iproute2"; exit 1; }
for p in $PORTS $APP_LOCAL_PORT; do
  if ss -ltnH "sport = :$p" | grep -q . && [ -z "$OURS" ]; then
    echo "!! Cổng $p đang được chương trình khác dùng:"; ss -ltnpH "sport = :$p" || true
    if [ "$p" = "$APP_LOCAL_PORT" ]; then
      echo "!! DỪNG, không thay đổi gì. Chọn cổng nội bộ khác, ví dụ thêm: APP_LOCAL_PORT=18080"
    else
      echo "!! DỪNG, không thay đổi gì. Chọn cổng khác, ví dụ: APP_PORT=8090 (và không dùng DOMAIN)."
    fi
    exit 1
  fi
done

if [ -n "${CHECK_ONLY:-}" ]; then
  echo "== CHỈ KIỂM TRA, không thay đổi gì =="
  echo "Cổng sẽ dùng: $PORTS (public), 127.0.0.1:$APP_LOCAL_PORT (nội bộ) — đều còn trống."
  if command -v docker >/dev/null 2>&1; then echo "Docker: đã có ($(docker --version)) — sẽ KHÔNG cài lại";
  else echo "Docker: chưa có — sẽ cài bằng get.docker.com"; fi
  echo "RAM: $(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo) MB; swap: $(swapon --show --noheadings | wc -l) thiết bị"
  echo "Ổ đĩa trống: $(df -h / | awk 'NR==2{print $4}') (cần khoảng 1 GB)"
  if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then echo "ufw: đang bật — chỉ THÊM luật cho cổng $PORTS";
  else echo "ufw: không bật — giữ nguyên, không đụng tới"; fi
  echo "Container đang chạy (sẽ không bị đụng tới):"; docker ps --format '  {{.Names}}  {{.Ports}}' 2>/dev/null || true
  exit 0
fi


echo "==> Cài gói cần thiết"
apt-get update -qq
apt-get install -y -qq --no-upgrade git curl ca-certificates openssl iproute2 >/dev/null

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Cài Docker"
  curl -fsSL https://get.docker.com | sh >/dev/null
fi
docker info >/dev/null 2>&1 || { echo "Docker chưa chạy. Kiểm tra: systemctl status docker"; exit 1; }

# Máy 1 GB RAM, chưa có swap: thêm 1 GB swap để build image không bị thiếu bộ nhớ
MEM_MB=$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo)
if [ "$MEM_MB" -lt 1500 ] && [ "$(swapon --show | wc -l)" = "0" ] && [ ! -f /swapfile ]; then
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
  URL="http://$IP"; [ "$APP_PORT" = "80" ] || URL="$URL:$APP_PORT"; OVERRIDE="deploy/compose.ip.yml"
fi
sed -i '/^APP_URL=/d' .env; echo "APP_URL=$URL" >> .env

sed -i '/^APP_PORT=/d; /^APP_LOCAL_PORT=/d' .env
echo "APP_PORT=$APP_PORT" >> .env; echo "APP_LOCAL_PORT=$APP_LOCAL_PORT" >> .env

# Tường lửa: chỉ thêm luật nếu ufw ĐÃ bật sẵn; không bao giờ tự bật/tắt
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  echo "==> ufw đang bật: thêm luật mở cổng $PORTS (giữ nguyên các luật cũ)"
  for p in $PORTS; do ufw allow "$p/tcp" >/dev/null; done
fi

echo "==> Build và chạy (lần đầu mất vài phút)"
docker compose -p "$PROJECT" --env-file .env -f docker-compose.yml -f "$OVERRIDE" up -d --build

PASS="$(grep '^APP_PASSWORD=' .env | cut -d= -f2-)"
echo
echo "============================================================"
echo " OSS Radar đã chạy:  $URL"
echo " Đăng nhập: tên gì cũng được, mật khẩu: $PASS"
echo " (mật khẩu lưu trong $DIR/.env — đổi xong chạy lại script)"
[ -z "$DOMAIN" ] && echo " Lưu ý: chưa có HTTPS. Nên trỏ tên miền về $IP rồi chạy lại với DOMAIN=..."
echo " Cập nhật code mới: chạy lại đúng lệnh cài đặt."
echo " Xem log: cd $DIR && docker compose -p $PROJECT -f docker-compose.yml -f $OVERRIDE logs -f"
echo " Gỡ bỏ:   cd $DIR && docker compose -p $PROJECT -f docker-compose.yml -f $OVERRIDE down"
echo "============================================================"

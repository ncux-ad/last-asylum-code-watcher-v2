#!/bin/sh
# Проверяет доступность fenix-clan.ru и fenix-clan.online, шлёт алерт в
# Telegram ТОЛЬКО при смене состояния (up→down, down→up) — иначе таймер,
# гоняемый каждые 10 минут, будет спамить сообщениями всё время, пока
# сайт лежит. Переиспользует бота/чат радара (тот же .env), отдельный
# токен не нужен.
set -eu

STATE_DIR="${HOME}/.local/state/fenix-uptime"
mkdir -p "$STATE_DIR"

ENV_FILE="${HOME}/last-asylum-code-watcher-v2/.env"
[ -f "$ENV_FILE" ] && . "$ENV_FILE"

send_telegram() {
  msg="$1"
  [ -z "${TELEGRAM_BOT_TOKEN:-}" ] && return 0
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    ${TELEGRAM_MESSAGE_THREAD_ID:+-d "message_thread_id=${TELEGRAM_MESSAGE_THREAD_ID}"} \
    --data-urlencode "text=${msg}" >/dev/null || true
}

check_one() {
  name="$1"; url="$2"
  state_file="${STATE_DIR}/${name}"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url" || echo "000")

  prev="up"
  [ -f "$state_file" ] && prev=$(cat "$state_file")

  if [ "$code" = "200" ]; then cur="up"; else cur="down"; fi

  if [ "$cur" != "$prev" ]; then
    if [ "$cur" = "down" ]; then
      send_telegram "⚠️ $url недоступен (код ответа: $code)"
    else
      send_telegram "✅ $url снова доступен"
    fi
  fi
  echo "$cur" > "$state_file"
}

check_one "ru" "https://fenix-clan.ru/"
check_one "online" "https://fenix-clan.online/"

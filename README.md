# Last Asylum: Plague Code Radar v2

Автоматический радар промокодов Last Asylum: Plague.

v2 добавляет:
- мониторинг нескольких сайтов;
- Google News RSS discovery;
- опциональный Discord listener;
- SQLite для локального запуска;
- переносимую JSON-базу для GitHub Actions;
- дедупликацию и историю наблюдений;
- confidence score;
- детектор появления/исчезновения кодов;
- Telegram notifications;
- статический web dashboard;
- GitHub Pages deployment;
- ручной запуск workflow;
- тесты.

## Архитектура

```text
Sites ───────┐
Google News ─┼──> detector ──> state.json ──> dashboard
Discord ─────┘          │
                        └────> Telegram
```

Discord — отдельный опциональный компонент. Для чтения сообщений бот должен быть добавлен в нужный Discord-сервер и иметь доступ к нужным каналам.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m watcher
```

## Telegram

Создайте Telegram bot и задайте:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## Discord listener

Установите зависимости:

```bash
pip install -r requirements-discord.txt
```

Задайте:

```text
DISCORD_BOT_TOKEN=
DISCORD_CHANNEL_IDS=123,456
```

Запустите:

```bash
python -m discord_listener
```

Listener сохраняет обнаруженные коды в `data/discord-discoveries.json`.
Для production лучше запускать его на небольшом VPS/домашнем сервере, а не в GitHub Actions.

## Ручная проверка кодов (опционально)

У игры есть официальный сайт редемпшна (`gevents.globallap.com/gamecode/index.html?gameId=440`), но вход там — через Facebook/Google OAuth или OTP, и код привязывается к конкретному серверу/персонажу. Автоматизировать этот вход в шедулере значило бы гонять чужой логин без участия человека — это отдельная модель доверия и риска по сравнению с чтением публичных страниц, поэтому радар этого не делает.

Вместо этого — `tools/verify_codes.py`, инструмент для оператора, не часть шедулера:

```bash
pip install -r requirements-manual-verify.txt
playwright install chromium
python tools/verify_codes.py
```

Скрипт открывает настоящий видимый браузер на странице редемпшна. Вход (OAuth/OTP), выбор сервера/персонажа и сам клик "Confirm" — всё делает человек. Скрипт только показывает список непроверенных кандидатов из `data/state.json` и сохраняет то, что вы сообщите (валиден/невалиден/уже использован/истёк, награда) в `data/manual_verifications.json` — локально, в git не коммитится, это ваш полный лог.

Кроме этого, лёгкая версия результата (`manual_verification: {result, reward, verified_at}`) сразу же пишется и в `data/state.json`, то есть попадает на публичный дашборд — реальная попытка редемпшна надёжнее эвристики по числу источников (код может быть "confirmed" тремя сайтами и при этом уже истёкшим). На дашборде это отдельный бейдж с подсказкой, что проверено на одном аккаунте/сервере, а не гарантированно для всех. `ok` дополнительно перезаписывает `reward` точным текстом награды из игры, `expired` — выставляет флаг `expired`.

### Быстрое добавление одного кода: `watcher/add_code.py`

Если код уже проверен в игре руками (например, кто-то прислал его вам напрямую) и городить браузерную сессию через `tools/verify_codes.py` ради одного кода не хочется — то же самое одной командой, без playwright:

```bash
python -m watcher.add_code LA30W7F2M --reward "200 алмазов"
# --result invalid|expired|used|not_found — если код не сработал
# --no-notify — не постить в Telegram, даже если result=ok
```

Заводит код в `data/state.json`, если его там ещё не было (источник `manual`; если он уже был подхвачен сканером как кандидат — просто дополняет ту запись, не задваивая источник), выставляет `manual_verification` так же, как `tools/verify_codes.py`, и для `--result ok` сразу постит в Telegram (как `watcher/manual_post.py`, но без отдельного шага). Не забудьте `cp data/state.json docs/state.json` и закоммитить, если публикуете вручную, а не через self-hosted таймер.

### Учебный инструмент: `tools/inspect_redemption_traffic.py`

Отдельный скрипт (не автоматизация, не часть проверки кодов) — открывает ту же страницу редемпшна в видимом браузере и логирует все сетевые запросы/ответы, которые она делает, в `data/redemption-traffic.jsonl` (в git не коммитится). Вход/выбор сервера/ввод кода — всё делает человек, скрипт только наблюдает, ничего не заполняет и не нажимает. Сделан из любопытства — понять, что именно скрывается за JS-фронтом (обычный REST-бэкенд? что-то ещё?), не для того, чтобы на этом строить автоматизацию — риски автоматического входа/ввода кодов те же, что описаны выше. Заголовки/поля, похожие на секреты (`token`, `auth`, `password`, `otp`, `session`, `cookie` в названии — без учёта регистра) затираются перед записью на диск, но это best-effort фильтр, не гарантия — просмотрите лог сами, прежде чем куда-то его показывать.

## Продакшен: self-hosted (VPS + systemd timer)

Основной прод-деплой с 2026-09-03 — не CI, а обычный `systemd --user` таймер на своём сервере. Причина: GitHub заблокировал аккаунт за скрапинг ~13 сайтов каждые 30 минут годами подряд (типичный abuse-репорт на IP GitHub Actions), а GitLab.com требует identity verification для запуска джобов на shared runners, которую не всегда получается пройти. Собственный сервер не зависит ни от того, ни от другого.

Файлы лежат в `deploy/`:

```bash
# на сервере, от обычного (не root) пользователя
git clone <репозиторий> ~/last-asylum-code-watcher-v2
cd ~/last-asylum-code-watcher-v2
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # заполнить TELEGRAM_BOT_TOKEN/CHAT_ID/MESSAGE_THREAD_ID

mkdir -p ~/.config/systemd/user
cp deploy/radar.service deploy/radar.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now radar.timer

# таймер должен пережить выход из SSH-сессии и перезагрузку:
loginctl enable-linger "$(whoami)"
```

Проверка:

```bash
systemctl --user list-timers radar.timer
journalctl --user -u radar.service -n 50 --no-pager
```

Частота — раз в 30 минут (`OnCalendar=*:0/30:00` в `deploy/radar.timer`); ранее уже стоял этот интервал, снижался до 2 часов после бана GitHub-аккаунта, затем сознательно возвращён — см. RUNBOOK.

Таймер запускает два шага подряд (оба — `ExecStart=` в `deploy/radar.service`): сканирование (`python -m watcher`), затем публикация свежего `data/state.json` на публичный сайт (см. ниже). Второй шаг помечен ведущим `-` — сбой публикации (сеть, недоступен хостинг сайта) не валит весь юнит.

## Публикация данных на fenix-clan.ru

Публичный сайт клана (`fenix-clan.ru`, зеркало `fenix-clan.online`) — **отдельный репозиторий**, [`fenix-clan-site`](https://gitlab.com/ncuxyLLla/fenix-clan-site) (выделен из этого 2026-09-04: сайт — не про скрапинг промокодов, у него свой дизайн/деплой/DNS/мониторинг, смешивать в одну историю смысла не было). Здесь, в радаре, живёт только отправляющая сторона — второй шаг `radar.service`:

```
senko: python -m watcher → data/state.json
     └─ ssh (ограниченный ключ) → hosting_vds:/var/www/fenix-clan.ru/promocodes/state.json
```

Ключ `~/.ssh/keys/id_ed25519_senko_to_hostingvds_fenix` на `senko` может **только** перезаписать этот один файл — на стороне `hosting_vds` в `~/.ssh/authorized_keys` у него принудительная команда:
```
command="cat > /var/www/fenix-clan.ru/promocodes/state.json",no-agent-forwarding,no-port-forwarding,no-pty,no-X11-forwarding,no-user-rc ssh-ed25519 AAAA... senko-fenix-state-sync
```
Что бы клиент ни попросил выполнить (`ssh ... 'whoami'` и т.п.) — реально выполнится только эта команда. Компрометация `senko` (публичный скрапер, самая внешняя точка во всей системе) не даёт shell-доступа на сервер с сайтом.

Всё остальное про сайт — статика, ассеты, nginx, DNS/TLS, SEO, мониторинг аптайма — в README/RUNBOOK репозитория `fenix-clan-site`.

## GitHub Actions (резервный вариант)

`.github/workflows/radar.yml` настроен и рабочий сам по себе, но требует незаблокированный аккаунт (см. RUNBOOK — сейчас заблокирован). `workflow_dispatch` с параметром `manual_code` постит один код в обход confidence-порога (см. `watcher/manual_post.py`), расписание — раз в 30 минут (см. выше про риск повторного бана). Нужны repository secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_MESSAGE_THREAD_ID`. Workflow коммитит `data/state.json`/`docs/state.json` обратно в репозиторий (`contents: write`) — в отличие от self-hosted варианта выше, который этого не делает.

GitLab CI (`.gitlab-ci.yml`, pipeline schedule) был настроен как второй резервный вариант при миграции с GitHub, но упёрся в identity verification для shared runners и стал избыточен, как только self-hosted на `senko` заработал стабильно — конфиг, расписание, CI/CD Variables и Project Access Token убраны (2026-09-03). GitLab-репозиторий остался просто зеркалом кода. Если понадобится снова — см. историю коммитов этого файла и RUNBOOK на дату миграции, там весь сетап описан.

## Dashboard

После включения GitHub Pages dashboard будет доступен по адресу:

`https://<user>.github.io/<repo>/`

(Сейчас недоступен — GitHub Pages завязан на GitHub Actions, который не гоняется из-за блокировки аккаунта, см. RUNBOOK. Self-hosted прод на VPS дашборд не обновляет, см. «Известное ограничение» выше.)

Он показывает:
- активные коды и кандидаты, с цветными статусами (confirmed/probable/candidate);
- предполагаемую награду и дату истечения (best-effort, распознаются из текста страницы-источника);
- отдельный бейдж для уже истёкших кодов;
- confidence и источники — сворачиваются по умолчанию, разворачиваются тапом по коду;
- первое/последнее обнаружение;
- график новых кодов за последние 30 дней;
- копирование кода тапом/кнопкой, адаптивная вёрстка под мобильные экраны.

## Важная оговорка

`confidence` — это эвристика, а не гарантия работоспособности кода. Один и тот же код может быть региональным, серверным, одноразовым или уже истечь.

Награда и дата истечения — тоже эвристика: парсятся из текста рядом с кодом на странице-источнике и могут отсутствовать, ошибаться или устаревать.

Радар не выполняет автоматическую активацию кодов и не хранит игровые логины/пароли. Проверка кодов через игровой redemption API сознательно не реализована — это требовало бы передавать серверу радара живые игровые credentials, что меняет модель доверия и рискует блокировкой аккаунта по ToS игры.

## Что мониторим

По умолчанию используются публичные страницы, которые сейчас фигурируют в экосистеме Last Asylum:
- Pocket Gamer;
- App-Time;
- LastAsylumPlague.com;
- LastAsylum.com;
- Last-Asylum.fun;
- LOTA;
- TopUpLive;
- BoostBot;
- GamsGo;
- LevelGeeks;
- GamesTaunch;
- ClashiVerse;
- ProGamePilot.

Список редактируется в `watcher/config.py`. Проверены: отдают 200 и реальные коды через текущий парсер, `robots.txt` не запрещает нужные пути. Не добавлены `lastasylumguide.com` (коды рендерятся через JS, в сыром HTML их нет — наш парсер JS не выполняет) и `ldshop.gg` (блокирует запросы без браузерных заголовков, 403).

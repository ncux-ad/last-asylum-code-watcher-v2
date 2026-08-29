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

Скрипт открывает настоящий видимый браузер на странице редемпшна. Вход (OAuth/OTP), выбор сервера/персонажа и сам клик "Confirm" — всё делает человек. Скрипт только показывает список непроверенных кандидатов из `data/state.json` и сохраняет то, что вы сообщите (валиден/невалиден/уже использован/истёк, награда) в `data/manual_verifications.json` — локально, в git не коммитится, так как результат верен для одного конкретного аккаунта/сервера, а не гарантированно для всех.

## GitHub Actions

Добавьте repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Workflow запускается каждые 30 минут, обновляет `data/state.json`, строит dashboard и публикует его в GitHub Pages.

Workflow имеет `contents: write`, потому что история кодов хранится непосредственно в Git-репозитории.

## Dashboard

После включения GitHub Pages dashboard будет доступен по адресу:

`https://<user>.github.io/<repo>/`

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
- LOTA.

Список редактируется в `watcher/config.py`.

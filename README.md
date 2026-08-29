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
- активные коды;
- кандидаты;
- вероятно истёкшие;
- количество источников;
- confidence;
- первое/последнее обнаружение;
- историю релизов;
- источники.

## Важная оговорка

`confidence` — это эвристика, а не гарантия работоспособности кода. Один и тот же код может быть региональным, серверным, одноразовым или уже истечь.

Радар не выполняет автоматическую активацию кодов и не хранит игровые логины/пароли.

## Что мониторим

По умолчанию используются публичные страницы, которые сейчас фигурируют в экосистеме Last Asylum:
- Pocket Gamer;
- App-Time;
- LastAsylumPlague.com;
- LastAsylum.com;
- Last-Asylum.fun;
- LOTA.

Список редактируется в `watcher/config.py`.

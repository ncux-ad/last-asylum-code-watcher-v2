# RUNBOOK

Оперативный справочник по эксплуатации Last Asylum: Plague Code Radar (v2). Что это и архитектура — в `README.md`, здесь только "что делать руками" и накопленные грабли.

Репозиторий: https://github.com/ncux-ad/last-asylum-code-watcher-v2 (аккаунт заблокирован GitHub с 2026-09-02, см. ниже) · зеркало: https://gitlab.com/ncuxyLLla/last-asylum-code-watcher-v2
Дашборд (GitHub Pages): https://ncux-ad.github.io/last-asylum-code-watcher-v2/ (недоступен, пока аккаунт заблокирован)
Публичный сайт: https://fenix-clan.ru/ и https://fenix-clan.ru/promocodes/ (на `hosting_vds`, см. README → «Публичный сайт: fenix-clan.ru»)
Прод (сканер): systemd-таймер на VPS `senko`, см. README → «Продакшен: self-hosted»

## Ежедневная рутина

1. Открыть дашборд, посмотреть, что нового наверху (сортировка: сначала подтверждённые вручную рабочие, дальше по confidence; истёкшие свёрнуты внизу).
2. Раз в несколько дней — прогнать ручную проверку новых кандидатов:
   ```bash
   cd last-asylum-code-watcher-v2
   pip install -r requirements-manual-verify.txt   # один раз
   playwright install chromium                      # один раз
   python tools/verify_codes.py
   ```
   Откроется браузер → войти в аккаунт (Facebook/Google/OTP) → выбрать сервер/персонажа → вернуться в терминал → Enter. Дальше скрипт по очереди даёт коды, вы вводите их на странице и сообщаете результат.

## Что отвечать в `tools/verify_codes.py`

| Ответ | Когда | Что происходит |
|---|---|---|
| `ok` | код принят, награда начислена | зелёный бейдж "Работает", `reward` перезаписывается точным текстом из игры, код поднимается в топ дашборда |
| `expired` | игра прямо говорит "истёк" | код уходит в свёрнутый блок "Истёкшие коды" внизу |
| `invalid` | код не принят, без уточнения причины | остаётся в общем списке с красным бейджем "Код недействителен" — используйте, если непонятно, `expired` это или `not_found` |
| `used` | код существует, но уже использован на этом аккаунте | остаётся в общем списке — код может ещё работать на других аккаунтах |
| `not_found` | игра говорит, что такого кода вообще нет (мобильное приложение отличает это от "истёк") | **код полностью удаляется** с дашборда и заносится в блок-лист — источники, которые продолжают его листить, больше не смогут его вернуть |
| `skip` | не хотите проверять сейчас | код остаётся кандидатом, появится в следующем прогоне |

Важно: `invalid` и `not_found` — разные вещи. `invalid` — "не сработало, причина неясна" (код остаётся видимым). `not_found` — "игра подтвердила, что кода не существует" (код вычищается). Если сайт-редемпшн просто пишет "invalid" без деталей, а мобильное приложение даёт точную причину — перепроверяйте через приложение, оно информативнее (так нашли, что `LA26LOVE` на самом деле `expired`, а не `invalid`).

## Как добавить источник

1. Проверить вручную, что источник вообще отдаёт коды через наш парсер (не JS-рендеринг, не блокирует по User-Agent), прежде чем добавлять в `watcher/config.py`:
   ```bash
   python3 -c "
   from watcher.sources import scan_source
   name, candidates = scan_source('test', 'https://example.com/codes')
   print(len(candidates), 'codes found')
   "
   ```
2. Проверить `robots.txt` домена — не запрещён ли путь, который собираемся скрейпить.
3. Добавить `("name", "url")` в `SOURCES` в `watcher/config.py`.
4. Прогнать тесты (`pytest`), закоммитить, задеплоить (см. ниже).

## Как вручную задеплоить / прогнать сканер

**Прод (self-hosted, VPS `senko`)** — обновить код и прогнать разово:

```bash
ssh senko "cd ~/last-asylum-code-watcher-v2 && git pull --ff-only && .venv/bin/python -m watcher"
```
Таймер и так гоняет каждые 2 часа (`systemctl --user list-timers radar.timer`) — ручной запуск нужен только чтобы сразу увидеть эффект от свежих изменений. Обновлённый локально код на `senko` доставляется через `git pull` из того ремоута, что там настроен, либо через `git bundle` + `scp`, если ремоут недоступен (так делали при первой миграции — см. историю коммитов этого файла).

**Пост одного уже известного кода в обход авто-порога confidence** (например, код подтверждён вручную оператором, но у него мало независимых источников):

```bash
ssh senko "cd ~/last-asylum-code-watcher-v2 && .venv/bin/python -m watcher.manual_post <CODE>"
```

**GitHub Actions** (пока аккаунт не заблокирован):
```bash
gh workflow run radar.yml --repo ncux-ad/last-asylum-code-watcher-v2 -f manual_code=<CODE или пусто>
gh run list --workflow=radar.yml --repo ncux-ad/last-asylum-code-watcher-v2 --limit 1
gh run watch <run-id> --repo ncux-ad/last-asylum-code-watcher-v2 --exit-status
```

**GitLab CI** (если поднят self-hosted runner — на shared runners упирается в identity verification):
```bash
curl --header "PRIVATE-TOKEN: <token>" --data '{"ref":"master"}' \
  "https://gitlab.com/api/v4/projects/<id>/pipeline"
# для ручного поста одного кода — добавить variables=[{key:MANUAL_CODE, value:<CODE>}] в тело запроса
```

## Публичный сайт (fenix-clan.ru): что делать руками

`state.json` на сайт доставляется автоматически (шаг в `radar.service`) — руками трогать нужно только саму статику и DNS/TLS.

**Обновить главную/промокоды-страницу после правок в `site/`:**
```bash
scp site/index.html hosting_vds:/tmp/fenix-index.html
scp site/promocodes/index.html hosting_vds:/tmp/fenix-promocodes-index.html
ssh hosting_vds "mv /tmp/fenix-index.html /var/www/fenix-clan.ru/index.html \
  && mv /tmp/fenix-promocodes-index.html /var/www/fenix-clan.ru/promocodes/index.html \
  && chown tot:tot /var/www/fenix-clan.ru/index.html /var/www/fenix-clan.ru/promocodes/index.html"
```

**Проверить, что state.json на сайте свежий:**
```bash
ssh hosting_vds "stat -c '%y %s bytes' /var/www/fenix-clan.ru/promocodes/state.json"
```
Сверить время с последним запуском `radar.service` на `senko` (`journalctl --user -u radar.service -n 5`).

**DNS (reg.ru):** управляется `~/server-init/regru-dns.sh` (SSL-сертификатная авторизация, credentials в `~/.config/regru/`, работает с любого IP):
```bash
DOMAIN=fenix-clan.ru ~/server-init/regru-dns.sh list
DOMAIN=fenix-clan.ru ~/server-init/regru-dns.sh set-a @ <IP>
DOMAIN=fenix-clan.ru ~/server-init/regru-dns.sh add AAAA @ <IPv6>
```

**TLS:** после того, как A/AAAA пропагировались (`dig @8.8.8.8 +short fenix-clan.ru A` возвращает нужный IP):
```bash
ssh hosting_vds "sudo certbot --nginx -d fenix-clan.ru -d www.fenix-clan.ru"
```
certbot сам допишет 443-блок в `/etc/nginx/sites-available/fenix-clan.ru` и настроит редирект с 80 — руками этот файл после этого не трогать.

## Работа с git: шедулер коммитит в фоне

Workflow сам коммитит `data/state.json`/`docs/state.json` при каждом прогоне (в том числе по расписанию). Если между вашим последним `git pull` и `git push` шедулер успел отработать — обычный push будет отклонён (`non-fast-forward`). Порядок действий:

```bash
git pull --rebase origin master
# если конфликт именно в data/state.json или docs/state.json:
git checkout --theirs data/state.json docs/state.json
# переприменить свои правки (ручные пометки, новый source и т.п.) поверх свежего state
git add data/state.json docs/state.json
git rebase --continue
git push
```
Не пытайтесь руками разрешать текстовый конфликт в JSON — легко сломать структуру. Проще взять чужую версию файла и переприменить свою правку программно (через `watcher.state.State`).

## Известные грабли (уже наступали, чтобы не наступать снова)

- **`lxml` был обязательной зависимостью, теперь убран.** Раньше `BeautifulSoup(r.text, "xml")` в `search.py` требовал `lxml` для парсинга Google News RSS. На сервере с Python 3.14 + свежим `libxml2` (2.15.2) сборка `lxml` 5.4.0 из исходников падает на несовместимости C API (const-корректность сигнатуры), готового wheel под cp314 ещё нет. Заменили на встроенный `xml.etree.ElementTree` — ноль внешних зависимостей, ноль нативной сборки. Если где-то в новом коде понадобится XML-парсинг — предпочитайте `xml.etree` вместо `BeautifulSoup(..., "xml")`, чтобы не тащить `lxml` обратно.
- **Джоба `pages` в `radar.yml` обязана указывать `ref: ${{ github.ref_name }}`** в `actions/checkout`. Без явного `ref` она чекаутит коммит, с которого стартовал ран, а не тот, что джоба `radar` только что запушила — из-за этого свежий `state.json` не попадал в задеплоенный дашборд.
- **Приватные файлы (gitignored) недоступны в GitHub Actions.** `data/manual_verifications.json` не в git — значит, раннер шедулера его никогда не увидит. Любая логика, которая должна переживать автоматический скан (например, блок-лист `not_found`), обязана жить внутри `state.json`, а не в приватных файлах. Наступили на это: первая версия удаления "не найденных" кодов не пережила следующий прогон, потому что источники их просто перевносили заново.
- **После первого пуша нового репозитория GitHub может не сразу зарегистрировать workflow** (`gh workflow run`/`workflow_dispatch` отдаёт 404 первые минуты). Помогает любой новый коммит, трогающий `.github/workflows/*.yml`.
- **Экстрактор кодов ловит ложные срабатывания** — уже отфильтровано, но если добавляете новый источник и видите мусор: обычные слова (нет цифр — `extractor.py` требует хотя бы одну цифру в коде), generic "счастливые" коды с lota.games (суффикс `666`/`777`/`888` — фильтруется `GENERIC_LUCKY_SUFFIX_RE`), обрывки UUID/хэшей (чисто hex-строки — фильтруются `HEX_ONLY_RE`).
- **GitHub забанил аккаунт (2026-09-02) — вероятная причина: скрапинг ~13 сайтов + Google News RSS каждые 30 минут годами подряд**, типичный триггер abuse-репортов на IP GitHub Actions. Снизили расписание до раз в 2 часа (и в `radar.yml`, и в `.gitlab-ci.yml`, и в `deploy/radar.timer`) и сделали `User-Agent` прозрачнее (частота + ссылка на репозиторий вместо непрозрачной строки). Если снова словите бан на любой платформе — сначала проверьте частоту опроса и `User-Agent`, а не сразу меняйте хостинг.
- **GitLab.com требует identity verification для запуска CI-джобов на shared runners** — это анти-abuse мера против крипто-майнинга, к скрапингу отношения не имеет и не всегда проходится. Обычный `git push`/`git pull` этому ограничению не подчиняется — только запуск пайплайна. Если verification не проходит — либо self-hosted GitLab Runner (тогда ограничение не действует, это уже не shared runner), либо не полагаться на GitLab CI вообще (как сейчас — прод на `senko`).
- **GitLab: protected-ветка и роль Project Access Token должны быть согласованы.** `PUSH_TOKEN` создан с ролью Developer (`access_level: 30`), а `master` по умолчанию защищена с `push_access_levels: Maintainers` (`access_level: 40`) — push из CI с таким токеном будет отклонён правами доступа. Либо поднимать роль токена/бота до Maintainer, либо (сделали так) разрешить push для Developers в Settings → Repository → Protected branches.
- **API-запросы на изменение CI/CD Variables и уровня доступа участников GitLab блокируются классификатором Claude Code** (даже с валидным токеном) — такие вещи нужно делать руками через веб-интерфейс GitLab, автоматизировать их через ассистента не получится.
- **`State.recalculate()` должен переживать item без ключа `sources`.** Тестовые фикстуры в `test_verify_codes.py` собирают `item` вручную (`{"code":..., "reward":..., "expired":...}`) без `sources`/`status`/`confidence` — раз `apply_manual_verification()` теперь сама вызывает `recalculate()` (чтобы ручная проверка `ok` сразу поднимала confidence/status, а не только на следующем `observe()`), `len(item["sources"])` кидал `KeyError`. Используйте `item.get("sources", {})`.
- **Свежезарегистрированный домен на reg.ru уже приходит с A-записями на парковочный IP** (`95.163.244.138` — это IP парковочной страницы reg.ru, не ошибка). `regru-dns.sh list` показывает их сразу после регистрации — не проверив, легко решить, что DNS "ещё не настроен", когда на самом деле нужно просто заменить существующую запись (`set-a`, не `add`, иначе будет дубль).
- **Не полагайтесь на публичный DNS-резолвер сразу после смены записи в панели reg.ru** — обновление NS-серверов reg.ru и последующая пропагация занимают от пары минут до пары часов. `dig @8.8.8.8 +short <домен> A` в первые минуты после правки может отдавать пусто даже при верно выставленной записи.
- **Публичный VPS, который занимается скрапингом (`senko`), не должен иметь shell-доступ к серверу с продакшен-сайтом.** Для доставки `state.json` на `hosting_vds` использован ограниченный ключ с `command="cat > <путь>"` в `authorized_keys` — что бы клиент ни запросил, выполнится только эта одна команда. Подключение с любым другим запросом (например, `whoami`) не выполняет его, а просто зависает на forced-команде в ожидании stdin — это ожидаемое поведение, а не баг; не пытайтесь "проверить" ограничение повторным подключением без стандартного ввода к тому же ключу — оно перезапишет/обнулит целевой файл ещё раз (shell truncates the file on open, до чтения stdin).

## Осознанно не сделано

- **Проверка кодов через официальный redemption API** (`gevents.globallap.com/gamecode/index.html?gameId=440`) не автоматизирована. Вход там — OAuth (Facebook/Google) или OTP, плюс привязка к серверу/персонажу; автоматизация логина — это либо нарушение ToS Google/Facebook/игры, либо угон реальной сессии пользователя. Вместо этого — `tools/verify_codes.py`, где логин и клик "Confirm" всегда делает человек.
- **Чтение официального Discord-сервера игры** не автоматизировано. У Discord нет OAuth-scope для чтения чужих сообщений; единственный технический способ — токен пользовательской сессии (self-bot), что прямо запрещено Discord Developer ToS и банится. Легитимный путь — попросить админов сервера добавить read-only бота (уже есть `discord_listener/`, просто нужны `DISCORD_CHANNEL_IDS` от добавленного бота).

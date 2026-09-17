# Разгортка корпусу на Hetzner VPS

Гэтая тэчка едзе на VPS у `/opt/corpus`. Тут няма нічога сакрэтнага - ключы і сэртыфікаты дадаюцца ўжо на сэрвэры.

## Як гэта працуе

```
CodeBuild ──push──> ECR instytutbelmovy-noske-prod (:latest + :<timestamp>)
                      ^
                      │ pull, systemd timer, штогадзіны
                 Hetzner VPS
                 caddy :443 ──> noske :80
                      ^
                      │ Hetzner Cloud Firewall: 443 толькі з Cloudflare
                 Cloudflare (Full strict)
```

**AWS ня мае ніякага доступу да VPS.** Наадварот: VPS мае IAM карыстальніка, які ўмее толькі чытаць адзін ECR рэпазыторый і больш нічога.

## Першапачатковая налада

### 1. AWS

```bash
./corpus_build/deploy-cloudformation.sh prod
aws iam create-access-key --user-name corpus-build-prod-vps-puller
```

Другая каманда пакажа сакрэт **адзін раз** - запішыце яго.

### 2. Hetzner

Стварыце сэрвэр: Debian 11+ або Ubuntu 22.04+ (правяралася на Ubuntu 26.04).

> ⚠️ **Толькі x86 (CX / CPX / CCX). Ня ARM (CAX).**
> CodeBuild зьбірае image на `amazonlinux2-x86_64`, гэта значыць `linux/amd64`.
> ARM-машыны ў Hetzner таньнейшыя, і спакуса ўзяць CAX вялікая - але image на іх проста не запусьціцца (`exec format error`).
> `provision.sh` спыніцца з памылкай, калі архітэктура ня amd64.

Дыск: **не менш за 3× памеру image** - адначасова ляжаць стары image, новы і оверлэй Docker'а. Памер image відаць у логах CodeBuild або праз `aws ecr describe-images`.
Гэта найбольш верагодная прычына, па якой усё зламаецца: машына, куды image улазіць адзін раз, але не двойчы, будзе маўкліва валіць кожную начную разгортку.

Стварыце Cloud Firewall і **прымацуйце яго да сэрвэра**:

| Порт | Пратакол | Крыніца |
|------|----------|---------|
| 443  | TCP      | дыяпазоны Cloudflare - https://www.cloudflare.com/ips-v4 (і `ips-v6`, калі ёсьць AAAA запіс) |
| 22   | TCP      | толькі ваш IP |

Выходны трафік не абмяжоўваем - праз яго ідзе pull з ECR.

### 3. Cloudflare

1. `A` запіс на IP сэрвэра, **proxied** (аранжавая хмарка).
2. SSL/TLS mode: **Full (strict)**.
3. SSL/TLS → Origin Server → Create Certificate (15 гадоў).
   Захаваць як `certs/origin.pem` і `certs/origin.key`.

### 4. Сэрвэр

```bash
ssh root@<vps>
mkdir -p /opt/corpus/certs
exit

scp -r corpus_build/vps/* root@<vps>:/opt/corpus/
scp origin.pem origin.key root@<vps>:/opt/corpus/certs/

ssh root@<vps>
cd /opt/corpus
chmod 600 certs/origin.key
cp .env.example .env && nano .env     # ECR_REGISTRY, ECR_REPOSITORY, DOMAIN
bash provision.sh                     # спытае AWS ключы з кроку 1
systemctl start corpus-deploy.service # першая разгортка
```

## CORS: выклікі API з bielkorpus.com

`noske.bielkorpus.com` - гэта іншы Origin, чым `bielkorpus.com`, таму браўзэр без загалоўка `Access-Control-Allow-Origin` не дасьць прачытаць адказ.
Загалоўкі дадае Caddy - noske нічога пра CORS ня ведае.

Дазволеныя `https://bielkorpus.com` і `https://www.bielkorpus.com` (ня ведаю навошта).

Каб дадаць яшчэ дамэн, праўце рэгулярку ў дзьвюх матчарах `Caddyfile` (`@cors_ok` і `@cors_preflight` - яны мусяць супадаць):

```
^https://(www\.)?bielkorpus\.com$
```

Тры рэчы, якія лёгка зрабіць няправільна:

- Preflight (`OPTIONS`) абрываецца ў Caddy і не ідзе да noske: Apache
  адказаў бы 200 без CORS-загалоўкаў і браўзэр заблякаваў бы запыт.

### Як прымяніць зьмены ў Caddyfile

```bash
docker compose -f /opt/corpus/docker-compose.yml restart caddy
```

⚠️ Менавіта `restart`, а **не** `caddy reload`: у глабальным блоку стаіць `admin off`, а reload ходзіць якраз праз admin API, таму не спрацуе.

### Праверка

```bash
curl -sSI -H "Origin: https://bielkorpus.com" \
  "https://noske.bielkorpus.com/bonito/run.cgi/corp_info?corpname=usie_teksty.conf" \
  | grep -i access-control
```

Мусіць вярнуць `access-control-allow-origin: https://bielkorpus.com`.

> Калі раптам уключыце кэшаваньне Cloudflare на гэтых шляхах - адказы зьмяняюцца ў залежнасьці ад `Origin`, і закэшаваны адказ без CORS-загалоўкаў будзе час ад часу ламаць запыты.
> `Vary: Origin` мы выстаўляем, але Cloudflare на бясплатным тарыфе яго не ўлічвае.
> Па змоўчаньні `.cgi` з query string не кэшуецца, так што зараз усё добра.

## Штодзённая эксплуатацыя

```bash
journalctl -u corpus-deploy -f            # лог разгорткі
systemctl list-timers corpus-deploy       # калі наступны запуск
systemctl start corpus-deploy.service     # разгарнуць зараз, не чакаючы таймера
docker compose -f /opt/corpus/docker-compose.yml ps
docker compose -f /opt/corpus/docker-compose.yml logs -f noske
df -h /var/lib/docker                     # месца на дыску
```

### Якая версія зараз задэплоеная

```bash
curl https://noske.bielkorpus.com/version.json    # commit noske і час зборкі бягучага корпуса
```

### Адкат на папярэдні image

У ECR заўсёды ляжаць 2 апошнія image (lifecycle policy). Знайсьці тэг:

```bash
aws ecr describe-images --repository-name instytutbelmovy-noske-prod \
    --query 'sort_by(imageDetails,&imagePushedAt)[*].imageTags' --output table
```

Потым у `/opt/corpus/docker-compose.yml` замяніць `:latest` на патрэбны тэг і:

```bash
docker compose up -d
```

⚠️ Пакуль тэг прыбіты, таймер больш не будзе прыносіць новыя зборкі - не забудзьцеся вярнуць `:latest`.

## Калі нешта не працуе

| Сымптом | Куды глядзець |
|---------|---------------|
| `docker compose pull` → `no basic auth credentials` | `/root/.docker/config.json` (ці правільны хост?), `/root/.aws/credentials` |
| Корпусы пустыя ў вэб-інтэрфэйсе | `docker compose exec noske ls /corpora` - калі пуста, нехта дадаў volume на `/corpora` і засланіў убудаваныя корпусы |
| 502 ад Cloudflare | кантэйнер `noske` не падняўся: `docker compose logs noske` |
| 521/522 ад Cloudflare | не дайшлі да 443: правілы Cloud Firewall, ці прымацаваны да сэрвэра |
| 526 ад Cloudflare | сэртыфікат Origin CA пратух або SSL mode не Full (strict) |
| **524 ад Cloudflare** | запыт быў даўжэй за 100 с - ліміт Cloudflare на бясплатным тарыфе. Гэта не памылка разгорткі, гл. ніжэй |
| Сайт ня робіць у часткі людзей | Cloudflare дадаў новы дыяпазон IP - абнавіце спіс у Cloud Firewall |
| Дыск скончыўся | `docker image prune -a -f`, потым павялічыць дыск |
| `CORS header 'Access-Control-Allow-Origin' missing` | Origin не супаў з рэгуляркай у `Caddyfile`, або Caddy не перазапушчаны пасьля праўкі. Праверце `curl -I -H "Origin: ..."` - гл. разьдзел пра CORS |
| `apt`: `does not have a Release file` пры ўсталёўцы Docker | сьпіс паказвае не на той дыстрыбутыў/рэліз. `provision.sh` сам прыбірае такі `/etc/apt/sources.list.d/docker.list` і перапісвае яго - дастаткова перазапусьціць скрыпт |

### Пра 524

Канкарданс на вялікім корпусе можа лічыцца даўжэй за 100 сэкунд, а Cloudflare на бясплатным тарыфе абрывае адказ на 100 с.
Caddy тут ужо чакае да 300 с, але Cloudflare усё роўна абарве раней.
Варыянты: падпамэн без праксі (шэрая хмарка) для доўгіх запытаў, або абмежаваць памер вынікаў у noske.

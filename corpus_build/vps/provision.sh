#!/bin/bash
# =============================================================================
# АДНАРАЗОВАЯ НАЛАДА HETZNER VPS
# Debian 11+ або Ubuntu 22.04+ , абавязкова x86_64 (ня ARM)
# Ідэмпатэнтны - можна запускаць паўторна
#
# Перад запускам:
#   1. скапіяваць гэтую тэчку ў /opt/corpus
#   2. стварыць /opt/corpus/.env (гл. .env.example)
#   3. пакласьці Cloudflare Origin CA сэртыфікат у /opt/corpus/certs/
#   4. мець пад рукой AWS ключы карыстальніка corpus-build-prod-vps-puller
# =============================================================================
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "❌ Патрэбны root"
    exit 1
fi

CORPUS_DIR="/opt/corpus"
AWS_REGION_DEFAULT="eu-central-1"

cd "$CORPUS_DIR"

# --- Праверкі перадумоў --------------------------------------------------
if [ ! -f "$CORPUS_DIR/.env" ]; then
    echo "❌ Няма $CORPUS_DIR/.env - скапіюйце .env.example і запоўніце"
    exit 1
fi

# shellcheck disable=SC1091
set -a; . "$CORPUS_DIR/.env"; set +a

for v in ECR_REGISTRY ECR_REPOSITORY DOMAIN; do
    if [ -z "${!v:-}" ]; then
        echo "❌ У .env не зададзена $v"
        exit 1
    fi
done

if [ ! -f "$CORPUS_DIR/certs/origin.pem" ] || [ ! -f "$CORPUS_DIR/certs/origin.key" ]; then
    echo "❌ Няма Cloudflare Origin CA сэртыфіката ў $CORPUS_DIR/certs/"
    echo "   Патрэбныя origin.pem і origin.key"
    exit 1
fi

# --- Вызначаем дыстрыбутыў -----------------------------------------------
# Docker трымае асобныя рэпазыторыі для debian і ubuntu. Калі ўзяць codename ад Ubuntu (напр. resolute), але шлях ад Debian,
# apt скажа "does not have a Release file" - таму бярэм і тое, і тое з /etc/os-release.
. /etc/os-release

DISTRO="${ID:-}"
CODENAME="${VERSION_CODENAME:-}"

case "$DISTRO" in
    ubuntu|debian) ;;
    *)
        # вытворныя (Mint, Raspbian, Pop!_OS...) - арыентуемся на ID_LIKE
        case " ${ID_LIKE:-} " in
            *ubuntu*) DISTRO="ubuntu"; CODENAME="${UBUNTU_CODENAME:-$CODENAME}" ;;
            *debian*) DISTRO="debian"; CODENAME="${DEBIAN_CODENAME:-$CODENAME}" ;;
            *)
                echo "❌ Дыстрыбутыў '${ID:-?}' не падтрымліваецца (трэба debian або ubuntu)"
                exit 1
                ;;
        esac
        ;;
esac

if [ -z "$CODENAME" ]; then
    echo "❌ Не выйшла вызначыць codename з /etc/os-release"
    exit 1
fi

echo "🖥️  Сыстэма: ${PRETTY_NAME:-$DISTRO} ($DISTRO/$CODENAME, $(dpkg --print-architecture))"

if [ "$(dpkg --print-architecture)" != "amd64" ]; then
    echo "❌ Архітэктура не amd64. Image зьбіраецца пад linux/amd64 на CodeBuild"
    echo "   і тут проста не запусьціцца. Патрэбны x86 сэрвэр (CX/CPX/CCX, ня CAX)."
    exit 1
fi

# Здымаем сьпіс Docker'а, калі ён паказвае не на той дыстрыбутыў ці рэліз (напр. пасьля няўдалага запуску): пакуль ён ляжыць,
# любы apt-get update валіцца з ненулявым кодам і скрыпт не даходзіць да месца, дзе гэты файл перапісваецца.
DOCKER_LIST="/etc/apt/sources.list.d/docker.list"
if [ -f "$DOCKER_LIST" ] && ! grep -q "linux/${DISTRO} ${CODENAME} " "$DOCKER_LIST"; then
    echo "🧹 Прыбіраем няправільны $DOCKER_LIST:"
    sed 's/^/     /' "$DOCKER_LIST"
    rm -f "$DOCKER_LIST"
fi

# --- Пакеты --------------------------------------------------------------
echo "📦 Усталёўваем пакеты..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg unattended-upgrades

# Docker з афіцыйнага рэпазыторыя (у дыстрыбутыве свой пакет бывае
# састарэлы і без compose plugin)
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    echo "🐳 Усталёўваем Docker..."

    DOCKER_REPO="https://download.docker.com/linux/${DISTRO}"

    # Правяраем, што Docker наогул выпускае пакеты пад гэты рэліз - інакш apt вываліць незразумелае "does not have a Release file"
    if ! curl -fsS --max-time 20 -o /dev/null "${DOCKER_REPO}/dists/${CODENAME}/Release"; then
        echo "❌ Docker ня мае рэпазыторыя для ${DISTRO}/${CODENAME}"
        echo "   Даступныя: ${DOCKER_REPO}/dists/"
        echo "   Або вазьміце сэрвэр са старэйшым LTS, або пастаўце docker.io"
        echo "   з рэпазыторыя дыстрыбутыва ўручную."
        exit 1
    fi

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL "${DOCKER_REPO}/gpg" | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] ${DOCKER_REPO} ${CODENAME} stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
else
    echo "✅ Docker ужо ёсьць"
fi
systemctl enable --now docker

# ECR credential helper: сам абнаўляе токен (ECR токен жыве 12 гадзін),
# таму ў таймеры не трэба ніякага docker login
echo "🔑 Усталёўваем amazon-ecr-credential-helper..."
if ! apt-get install -y -qq amazon-ecr-credential-helper 2>/dev/null; then
    # На Ubuntu пакет ляжыць у universe, які можа быць выключаны
    if [ "$DISTRO" = "ubuntu" ]; then
        echo "   Уключаем universe..."
        apt-get install -y -qq software-properties-common
        add-apt-repository -y universe
        apt-get update -qq
        apt-get install -y -qq amazon-ecr-credential-helper
    else
        echo "❌ Не выйшла паставіць amazon-ecr-credential-helper"
        exit 1
    fi
fi

if ! command -v docker-credential-ecr-login >/dev/null 2>&1; then
    echo "❌ docker-credential-ecr-login ня знойдзены пасьля ўсталёўкі"
    exit 1
fi

# --- AWS credentials для pull --------------------------------------------
mkdir -p /root/.aws /root/.docker
chmod 700 /root/.aws

if [ ! -f /root/.aws/credentials ]; then
    echo ""
    echo "🔑 Патрэбныя ключы IAM карыстальніка corpus-build-prod-vps-puller."
    echo "   На машыне з адмінскім доступам:"
    echo "   aws iam create-access-key --user-name corpus-build-prod-vps-puller"
    echo ""
    read -rp "AWS_ACCESS_KEY_ID: " AKID
    read -rsp "AWS_SECRET_ACCESS_KEY: " ASAK; echo ""

    cat > /root/.aws/credentials <<EOF
[default]
aws_access_key_id = ${AKID}
aws_secret_access_key = ${ASAK}
EOF
    chmod 600 /root/.aws/credentials
    echo "✅ /root/.aws/credentials створаны"
else
    echo "✅ /root/.aws/credentials ужо ёсьць"
fi

cat > /root/.aws/config <<EOF
[default]
region = ${AWS_REGION:-$AWS_REGION_DEFAULT}
EOF

# Docker бярэ credentials з helper'а для нашага ECR рэгістра
cat > /root/.docker/config.json <<EOF
{
  "credHelpers": {
    "${ECR_REGISTRY}": "ecr-login"
  }
}
EOF
chmod 600 /root/.docker/config.json
echo "✅ Docker credential helper наладжаны на ${ECR_REGISTRY}"

# --- systemd -------------------------------------------------------------
echo "⚙️ Наладжваем systemd..."
chmod +x "$CORPUS_DIR/deploy.sh"
install -m 0644 "$CORPUS_DIR/corpus-deploy.service" /etc/systemd/system/
install -m 0644 "$CORPUS_DIR/corpus-deploy.timer"   /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now corpus-deploy.timer

# --- Аўтаматычныя абнаўленьні бясьпекі -----------------------------------
dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true

echo ""
echo "✅ Налада завершаная"
echo ""
echo "⚠️  Фаервол НЕ наладжваецца тут - ён у панэлі Hetzner Cloud."
echo "    Пераканайцеся, што Cloud Firewall прымацаваны да сэрвэра:"
echo "      443/tcp - толькі з дыяпазонаў Cloudflare (cloudflare.com/ips-v4)"
echo "      22/tcp  - толькі з вашага IP"
echo "    ufw тут не дапаможа: Docker піша свае правілы ў nat/FORWARD,"
echo "    якія праходзяць ПЕРАД ланцужком INPUT, дзе сядзіць ufw."
echo ""
echo "Далей:"
echo "  systemctl start corpus-deploy.service   # першая разгортка"
echo "  journalctl -u corpus-deploy -f          # сачыць за логам"
echo "  systemctl list-timers corpus-deploy     # калі наступны запуск"

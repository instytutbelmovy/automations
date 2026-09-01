#!/bin/bash
# =============================================================================
# ЦЯГНЕ СЬВЕЖЫ IMAGE З ECR І ПЕРАЗАПУСКАЕ КОРПУС
# Запускаецца праз corpus-deploy.timer (штогадзіны)
# =============================================================================
set -euo pipefail

CORPUS_DIR="/opt/corpus"
cd "$CORPUS_DIR"

# shellcheck disable=SC1091
set -a; . "$CORPUS_DIR/.env"; set +a

IMAGE="${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"

# Не даем дзьвюм копіям ісьці адначасова (напр. таймер + ручны запуск)
exec 9>/var/lock/corpus-deploy.lock
if ! flock -n 9; then
    echo "Разгортка ўжо выконваецца, выходзім"
    exit 0
fi

current_id() {
    docker image inspect --format '{{.Id}}' "$IMAGE" 2>/dev/null || echo "none"
}

BEFORE=$(current_id)

# Сьцягваем ДА перазапуску: прастой = толькі рэстарт кантэйнера (сэкунды), а не час запампоўкі шматгігабайтнага image
echo "Цягнем $IMAGE ..."
docker compose pull --quiet

AFTER=$(current_id)

if [ "$BEFORE" = "$AFTER" ]; then
    echo "Image не зьмяніўся, нічога не перазапускаем"
    # усё роўна пераканаемся, што ўсё паднятае (напр. пасьля збою)
    docker compose up -d
    exit 0
fi

echo "Новы image: ${BEFORE:0:19} -> ${AFTER:0:19}"
docker compose up -d

# Стары image стаў dangling (тэг latest зьехаў) - прыбіраем, інакш дыск скончыцца праз некалькі начэй
docker image prune -f

echo "Разгортка завершаная"
docker compose ps

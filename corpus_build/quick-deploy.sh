#!/bin/bash

# =============================================================================
# ХУТКІ ДЭПЛОЙМЭНТ КОДУ
# =============================================================================

# Адключаем pager для AWS CLI
export AWS_PAGER=""

# Параметр асяроддзя (dev або prod)
ENVIRONMENT=${1:-dev}

# Правяраем дапушчальныя значэнні
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    echo "❌ Памылка: ENVIRONMENT павінен быць 'dev' або 'prod'"
    echo "Выкарыстанне: $0 [dev|prod]"
    echo "Па змаўчанні: dev"
    exit 1
fi

# Назва стэка з суфіксам асяроддзя
STACK_NAME="corpus-build-${ENVIRONMENT}"
REGION="eu-central-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="instytutbelmovy-corpus-build-${ENVIRONMENT}"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
FUNCTION_NAME="${STACK_NAME}-function"

echo "⚡ Хуткі дэплоймэнт коду для асяроддзя: ${ENVIRONMENT}"
echo "📦 Стэк: ${STACK_NAME}"
echo "🏗️ ECR Repository: ${ECR_REPOSITORY_NAME}"
echo ""

# Правяраем ці існуе лямбда функцыя
echo "Правяраем існаваньне лямбда функцыі..."
if ! aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo "❌ Лямбда функцыя не існуе. Выкарыстоўвайце поўны дэплоймэнт: ./corpus_build/deploy-cloudformation.sh ${ENVIRONMENT}"
    exit 1
fi

# Сабраць Docker image
echo "🏗️ Зборка Docker image..."
if ! docker build \
    --platform linux/amd64 \
    --provenance=false \
    -t ${STACK_NAME} \
    -f corpus_build/Dockerfile .; then
    echo "❌ Памылка пры зборцы Docker image. Спыняем выкананьне."
    exit 1
fi

# Аўтарызавацца ў ECR
echo "🔐 Аўтарызацыя ў ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Тэгнуць і выпхнуць image
echo "📤 Выпханьне Docker image..."
docker tag ${STACK_NAME}:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

# Абнавіць код лямбда функцыі
echo "🔄 Абнаўленьне лямбда функцыі..."
if ! aws lambda update-function-code \
    --function-name ${FUNCTION_NAME} \
    --image-uri ${ECR_URI}:latest \
    --region ${REGION}; then
    echo "❌ Памылка пры абнаўленьні лямбда функцыі. Спыняем выкананьне."
    exit 1
fi

# Чакаем сканчэньня абнаўленьня
echo "Чакаем сканчэньня абнаўленьня лямбда функцыі..."
aws lambda wait function-updated --function-name ${FUNCTION_NAME} --region ${REGION}

if [ $? -eq 0 ]; then
    echo "✅ Хуткі дэплоймэнт выкананы пасьпяхова!"
    
    # Выводзім інфармацыю пра функцыю
    echo "=== ІНФАРМАЦЫЯ ПРА ЛЯМБДА ФУНКЦЫЮ ==="
    aws lambda get-function \
        --function-name ${FUNCTION_NAME} \
        --region ${REGION} \
        --query 'Configuration.[FunctionName,Runtime,Timeout,MemorySize,LastModified]' \
        --output table
    
    echo ""
    echo "📋 Інструкцыі:"
    echo "1. Лямбда функцыя: ${FUNCTION_NAME}"
    echo "2. CloudWatch Logs: /aws/lambda/${FUNCTION_NAME}"
    echo "3. ECR Repository: ${ECR_REPOSITORY_NAME}"
    echo "4. Для поўнага дэплоймэнту: ./corpus_build/deploy-cloudformation.sh ${ENVIRONMENT}"
    
else
    echo "❌ Памылка пры абнаўленьні лямбда функцыі"
    echo "Праверце CloudWatch Logs для дэталяў"
fi 
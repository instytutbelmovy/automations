#!/bin/bash

# =============================================================================
# ХУТКІ ДЭПЛОЙМЭНТ КОДУ ФУНКЦЫІ
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
STACK_NAME="verti-converter-${ENVIRONMENT}"
REGION="eu-central-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ECR рэпазіторый з суфіксам асяроддзя
ECR_REPOSITORY_NAME="ibm-verti-converter-${ENVIRONMENT}"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

# Назва Lambda функцыі
FUNCTION_NAME="${STACK_NAME}-function"

# =============================================================================
# СКРЫПТ ХУТКАГА ДЭПЛОЙМЭНТУ
# =============================================================================

echo "⚡ Хуткі дэплоймэнт коду для асяроддзя: ${ENVIRONMENT}"
echo "📦 Стэк: ${STACK_NAME}"
echo "📁 ECR Repository: ${ECR_REPOSITORY_NAME}"
echo "🔧 Lambda Function: ${FUNCTION_NAME}"
echo ""

# Правяраем ці існуе Lambda функцыя
echo "Правяраем існаванне Lambda функцыі..."
if ! aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo "❌ Lambda функцыя ${FUNCTION_NAME} не існуе"
    echo "Выкарыстоўвайце поўны дэплоймэнт: ./devops/deploy-cloudformation.sh ${ENVIRONMENT}"
    exit 1
fi
echo "✅ Lambda функцыя існуе"

# Будуем Docker image
echo "Будуем Docker image..."
if ! docker build --platform linux/amd64 --provenance=false -t ${STACK_NAME} -f devops/Dockerfile .; then
    echo "❌ Памылка пры зборцы Docker image. Спыняем выкананне."
    exit 1
fi
echo "✅ Docker image паспяхова пабудаваны"

# Аўтарызуемся ў ECR
echo "Аўтарызуемся ў ECR..."
if ! aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_URI}; then
    echo "❌ Памылка аўтарызацыі ў ECR. Спыняем выкананне."
    exit 1
fi

# Тэгаваем і пушаем image
echo "Пушаем Docker image ў ECR..."
docker tag ${STACK_NAME}:latest ${ECR_URI}:latest
if ! docker push ${ECR_URI}:latest; then
    echo "❌ Памылка пры пушаванні Docker image. Спыняем выкананне."
    exit 1
fi
echo "✅ Docker image паспяхова запушан у ECR"

# Абнаўляем Lambda функцыю
echo "Абнаўляем Lambda функцыю..."
if ! aws lambda update-function-code \
    --function-name ${FUNCTION_NAME} \
    --image-uri ${ECR_URI}:latest \
    --region ${REGION}; then
    echo "❌ Памылка пры абнаўленні Lambda функцыі. Спыняем выкананне."
    exit 1
fi
echo "✅ Lambda функцыя паспяхова абноўлена"

# Чакаем завершэння абнаўлення
echo "Чакаем завершэння абнаўлення..."
aws lambda wait function-updated --function-name ${FUNCTION_NAME} --region ${REGION}

if [ $? -eq 0 ]; then
    echo "✅ Хуткі дэплоймэнт завершаны паспяхова!"
    
    # Выводзім інфармацыю пра функцыю
    echo "=== ІНФАРМАЦЫЯ ПРА ФУНКЦЫЮ ==="
    aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} \
        --query 'Configuration.[FunctionName,Runtime,Timeout,MemorySize,LastModified]' \
        --output table
else
    echo "❌ Памылка пры абнаўленні функцыі"
fi 
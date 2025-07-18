#!/bin/bash

# =============================================================================
# КАНФІГУРАЦЫЯ РАЗГОРТКІ
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

# S3 бакеты ў залежнасці ад асяроддзя
if [[ "$ENVIRONMENT" == "dev" ]]; then
    INPUT_BUCKET="ibm-editor-dev"
    OUTPUT_BUCKET="ibm-vert-dev"
else
    INPUT_BUCKET="ibm-editor"
    OUTPUT_BUCKET="ibm-vert"
fi

# Налады логавання
LOG_LEVEL="INFO"

# =============================================================================
# СКРЫПТ РАЗГОРТКІ
# =============================================================================

echo "🚀 Пачынаем разгортку для асяроддзя: ${ENVIRONMENT}"
echo "📦 Стэк: ${STACK_NAME}"
echo "📁 ECR Repository: ${ECR_REPOSITORY_NAME}"
echo "📥 Input Bucket: ${INPUT_BUCKET}"
echo "📤 Output Bucket: ${OUTPUT_BUCKET}"
echo ""

# Правяраем ці існуе стэк
if aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo "Стэк ${STACK_NAME} ужо існуе. Абнаўляем..."
    OPERATION="update-stack"
else
    echo "Ствараем новы стэк ${STACK_NAME}..."
    OPERATION="create-stack"
fi

# Будуем Docker image
echo "Будуем Docker image..."
if ! docker build --platform linux/amd64 --provenance=false -t ${STACK_NAME} -f devops/Dockerfile .; then
    echo "❌ Памылка пры зборцы Docker image. Спыняем выкананне."
    exit 1
fi
echo "✅ Docker image паспяхова пабудаваны для linux/amd64"

# Ствараем ECR рэпазіторый (калі не існуе)
echo "Правяраем ECR repository..."
if ! aws ecr describe-repositories --repository-names ${ECR_REPOSITORY_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo "Ствараем ECR repository..."
    aws ecr create-repository --repository-name ${ECR_REPOSITORY_NAME} --region ${REGION}
    
    # Наладжваем lifecycle policy
    echo "Наладжваем lifecycle policy..."
    aws ecr put-lifecycle-policy \
        --repository-name ${ECR_REPOSITORY_NAME} \
        --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep last 3 images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": 3
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }' \
        --region ${REGION}
    
    echo "✅ ECR repository створаны з lifecycle policy"
else
    echo "ℹ️ ECR repository ужо існуе"
fi

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

# Разгортваем CloudFormation стэк
echo "Разгортваем CloudFormation стэк..."
if ! aws cloudformation ${OPERATION} \
    --stack-name ${STACK_NAME} \
    --template-body file://devops/template.yaml \
    --parameters \
        ParameterKey=InputBucket,ParameterValue=${INPUT_BUCKET} \
        ParameterKey=OutputBucket,ParameterValue=${OUTPUT_BUCKET} \
        ParameterKey=LogLevel,ParameterValue=${LOG_LEVEL} \
        ParameterKey=ECRRepositoryName,ParameterValue=${ECR_REPOSITORY_NAME} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}; then
    echo "❌ Памылка пры разгортцы CloudFormation стэка. Спыняем выкананне."
    exit 1
fi

# Чакаем завершэння разгорткі
echo "Чакаем завершэння разгорткі..."
if [ "$OPERATION" = "create-stack" ]; then
    aws cloudformation wait stack-create-complete \
        --stack-name ${STACK_NAME} \
        --region ${REGION}
else
    aws cloudformation wait stack-update-complete \
        --stack-name ${STACK_NAME} \
        --region ${REGION}
fi

if [ $? -eq 0 ]; then
    echo "✅ Разгортка завершана паспяхова!"
    
    # Наладжваем ReservedConcurrencyLimit пасля стварэння функцыі
    echo "Наладжваем ReservedConcurrencyLimit..."
    aws lambda put-function-concurrency \
        --function-name ${STACK_NAME}-function \
        --reserved-concurrent-executions 1 \
        --region ${REGION} 2>/dev/null || echo "ℹ️ ReservedConcurrencyLimit ужо наладжаны або не патрэбны"
    
    # Выводзім вынікі
    echo "=== ВЫНІКІ РАЗГОРТКІ ==="
    aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --region ${REGION} \
        --query 'Stacks[0].Outputs' \
        --output table
else
    echo "❌ Памылка пры разгортцы"
    echo "Праверце логі:"
    aws cloudformation describe-stack-events \
        --stack-name ${STACK_NAME} \
        --region ${REGION} \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output table
fi 
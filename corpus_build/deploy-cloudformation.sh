#!/bin/bash

# =============================================================================
# ПОЎНЫ ДЭПЛОЙМЭНТ З CLOUDFORMATION
# =============================================================================

# Адключаем pager для AWS CLI
export AWS_PAGER=""

# Параметр асяроддзя (dev або prod)
ENVIRONMENT=${1:-dev}

# Правяраем дапушчальныя значэньні
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    echo "❌ Памылка: ENVIRONMENT павінен быць 'dev' або 'prod'"
    echo "Выкарыстаньне: $0 [dev|prod]"
    echo "Па змоўчаньні: dev"
    exit 1
fi

# Назва стэка з суфіксам асяроддзя
STACK_NAME="corpus-build-${ENVIRONMENT}"
REGION="eu-central-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="ibm-corpus-build-${ENVIRONMENT}"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

# S3 buckets
if [ "$ENVIRONMENT" = "dev" ]; then
    INPUT_BUCKET="ibm-vert-dev"
else
    INPUT_BUCKET="ibm-vert"
fi

echo "🚀 Поўны дэплоймэнт для асяроддзя: ${ENVIRONMENT}"
echo "📦 Стэк: ${STACK_NAME}"
echo "🏗️ ECR Repository: ${ECR_REPOSITORY_NAME}"
echo "📁 Input Bucket: ${INPUT_BUCKET}"
echo ""

# Праверыць ці існуе ECR repository
echo "Правяраем ECR repository..."
if ! aws ecr describe-repositories --repository-names ${ECR_REPOSITORY_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo "❌ ECR repository не існуе. Ствараем..."
    if ! aws ecr create-repository --repository-name ${ECR_REPOSITORY_NAME} --region ${REGION}; then
        echo "❌ Памылка пры стварэньні ECR repository. Спыняем выкананьне."
        exit 1
    fi
    echo "✅ ECR repository створаны"
    # Паўза каб пераканацца што repository цалкам створаны
    sleep 5
else
    echo "✅ ECR repository ужо існуе"
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

# Тэгнуць і запушыць image
echo "📤 Пушаванне Docker image..."
docker tag ${STACK_NAME}:latest ${ECR_URI}:latest
if ! docker push ${ECR_URI}:latest; then
    echo "❌ Памылка пры выпханьні Docker image. Спыняем выкананьне."
    exit 1
fi

# Праверыць ці image пасьпяхова запханы
echo "Правяраем ці image запханы..."
if ! aws ecr describe-images --repository-name ${ECR_REPOSITORY_NAME} --image-ids imageTag=latest --region ${REGION} >/dev/null 2>&1; then
    echo "❌ Docker image ня знойдзены ў ECR. Спыняем выкананьне."
    exit 1
fi
echo "✅ Docker image пасьпяхова запханы ў ECR"

# Праверыць ці існуе CloudFormation стэк
echo "Правяраем CloudFormation стэк..."
if aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo "📝 Стэк існуе, абнаўляем..."
    OPERATION="update-stack"
else
    echo "🆕 Стэк не існуе, ствараем..."
    OPERATION="create-stack"
fi

# Запускаем CloudFormation
echo "Запускаем CloudFormation ${OPERATION}..."
if ! aws cloudformation ${OPERATION} \
    --stack-name ${STACK_NAME} \
    --template-body file://corpus_build/template.yaml \
    --parameters \
        ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
        ParameterKey=InputBucket,ParameterValue=${INPUT_BUCKET} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}; then
    
    if [ "$OPERATION" = "update-stack" ]; then
        echo "❌ Памылка пры абнаўленьні стэка"
    else
        echo "❌ Памылка пры стварэньні стэка"
    fi

    aws cloudformation describe-stack-events --stack-name ${STACK_NAME} \
     --region ${REGION} --query \
     'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`ROLLBACK_COMPLETE`].[LogicalResourceId,ResourceType,ResourceStatus,ResourceStatusReason]' \
     --output table

    exit 1
fi

# Чакаем завершэньня аперацыі
echo "Чакаем завершэньня CloudFormation аперацыі..."
if [ "$OPERATION" = "create-stack" ]; then
    aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME} --region ${REGION}
else
    aws cloudformation wait stack-update-complete --stack-name ${STACK_NAME} --region ${REGION}
fi

if [ $? -eq 0 ]; then
    echo "✅ Разгортка завершаная пасьпяхова!"
    
    # Выводзім інфармацыю пра стэк
    echo "=== ІНФАРМАЦЫЯ ПРА СТЭК ==="
    aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --region ${REGION} \
        --query 'Stacks[0].[StackName,StackStatus,CreationTime]' \
        --output table
    
    # Выводзім Outputs
    echo ""
    echo "=== OUTPUTS ==="
    aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --region ${REGION} \
        --query 'Stacks[0].Outputs' \
        --output table
    
    echo ""
    echo "📋 Інструкцыі:"
    echo "1. Lambda функцыя: corpus-build-${ENVIRONMENT}-function"
    echo "2. CodeBuild праект: corpus-build-${ENVIRONMENT}"
    echo "3. ECR Repository: ${ECR_REPOSITORY_NAME}"
    echo "4. CloudWatch Logs: /aws/lambda/corpus-build-${ENVIRONMENT}-function"
    echo "5. EventBridge Rule: corpus-build-trigger-${ENVIRONMENT}"
    
else
    echo "❌ Памылка пры разгортцы стэка"
    aws cloudformation describe-stack-events --stack-name ${STACK_NAME} \
     --region ${REGION} --query \
     'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`ROLLBACK_COMPLETE`].[LogicalResourceId,ResourceType,ResourceStatus,ResourceStatusReason]' \
     --output table
fi 
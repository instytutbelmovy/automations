#!/bin/bash

# =============================================================================
# КАНФІГУРАЦЫЯ АЧЫСТКІ І РАЗГОРТКІ
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

# Назвы рэсурсаў для выдалення
FUNCTION_NAME="${STACK_NAME}-function"
ROLE_NAME="${STACK_NAME}-lambda-role"

# =============================================================================
# СКРЫПТ АЧЫСТКІ І РАЗГОРТКІ
# =============================================================================

echo "🧹 Ачыстка і перазапуск разгорткі для асяроддзя: ${ENVIRONMENT}"
echo "📦 Стэк: ${STACK_NAME}"
echo ""

# Правяраем статус стэка
echo "Правяраем статус стэка ${STACK_NAME}..."
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "STACK_NOT_FOUND")

echo "Статус стэка: ${STACK_STATUS}"

# Калі стэк у ROLLBACK_COMPLETE стане, выдаляем яго
if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "❌ Стэк у ROLLBACK_COMPLETE стане. Выдаляем..."
    aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}
    
    echo "Чакаем выдалення стэка..."
    aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME} --region ${REGION}
    
    if [ $? -eq 0 ]; then
        echo "✅ Стэк паспяхова выдалены"
    else
        echo "❌ Памылка пры выдаленні стэка"
        exit 1
    fi
elif [ "$STACK_STATUS" = "STACK_NOT_FOUND" ]; then
    echo "ℹ️ Стэк не існуе, можна ствараць новы"
else
    echo "ℹ️ Стэк у стане: ${STACK_STATUS}"
    read -p "Выдаліць існуючы стэк? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Выдаляем стэк..."
        aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}
        aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME} --region ${REGION}
    else
        echo "Спыняем выкананне"
        exit 1
    fi
fi

# Выдаляем Lambda function калі яна існуе
echo "Правяраем Lambda function ${FUNCTION_NAME}..."
if aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo "Выдаляем Lambda function..."
    aws lambda delete-function --function-name ${FUNCTION_NAME} --region ${REGION}
    echo "✅ Lambda function выдалена"
fi

# Выдаляем IAM role калі ён існуе
echo "Правяраем IAM role ${ROLE_NAME}..."
if aws iam get-role --role-name ${ROLE_NAME} >/dev/null 2>&1; then
    echo "Выдаляем IAM role..."
    # Спачатку выдаляем attached policies
    aws iam list-attached-role-policies --role-name ${ROLE_NAME} --query 'AttachedPolicies[].PolicyArn' --output text | xargs -I {} aws iam detach-role-policy --role-name ${ROLE_NAME} --policy-arn {}
    # Затым выдаляем inline policies
    aws iam list-role-policies --role-name ${ROLE_NAME} --query 'PolicyNames[]' --output text | xargs -I {} aws iam delete-role-policy --role-name ${ROLE_NAME} --policy-name {}
    # Нарэшце выдаляем role
    aws iam delete-role --role-name ${ROLE_NAME}
    echo "✅ IAM role выдалена"
fi

echo ""
echo "🚀 Пачынаем чыстую разгортку для асяроддзя: ${ENVIRONMENT}..."
echo ""

# Запускаем разгортку з перадачай параметра асяроддзя
./verti_conversion/deploy-cloudformation.sh ${ENVIRONMENT} 
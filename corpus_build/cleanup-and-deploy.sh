#!/bin/bash

# =============================================================================
# АЧЫСТКА І ПЕРАЗАПУСК СТЭКА
# =============================================================================

# Адключаем pager для AWS CLI
export AWS_PAGER=""

# Параметр асяроддзя (dev або prod)
ENVIRONMENT=${1:-dev}

# Правяраем дапушчальныя значэньні
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    echo "❌ Памылка: ENVIRONMENT павінен быць 'dev' або 'prod'"
    echo "Выкарыстанне: $0 [dev|prod]"
    echo "Па змаўчанні: dev"
    exit 1
fi

# Назва стэка з суфіксам асяроддзя
STACK_NAME="corpus-build-${ENVIRONMENT}"
REGION="eu-central-1"

# =============================================================================
# СКРЫПТ АЧЫСТКІ І ПЕРАЗАПУСКУ
# =============================================================================

echo "🧹 Ачыстка і перазапуск для асяроддзя: ${ENVIRONMENT}"
echo "📦 Стэк: ${STACK_NAME}"
echo ""

# Правяраем стан стэка
echo "Правяраем стан CloudFormation стэка..."
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "STACK_NOT_FOUND")

echo "Статус стэка: ${STACK_STATUS}"

# Калі стэк у ROLLBACK_COMPLETE стане, выдаляем яго
if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "🗑️ Стэк у ROLLBACK_COMPLETE стане, выдаляем..."
    
    if aws cloudformation delete-stack \
        --stack-name ${STACK_NAME} \
        --region ${REGION}; then
        
        echo "⏳ Чакаем выдалення стэка..."
        aws cloudformation wait stack-delete-complete \
            --stack-name ${STACK_NAME} \
            --region ${REGION}
        
        if [ $? -eq 0 ]; then
            echo "✅ Стэк паспяхова выдалены"
        else
            echo "❌ Памылка пры выдаленні стэка"
            exit 1
        fi
    else
        echo "❌ Памылка пры выдаленні стэка"
        exit 1
    fi
elif [ "$STACK_STATUS" = "STACK_NOT_FOUND" ]; then
    echo "ℹ️ Стэк не існуе, ствараем новы..."
else
    echo "ℹ️ Стэк у нармальным стане, абнаўляем..."
fi

# Запускаем разгортку з перадачай параметра асяроддзя
echo "🚀 Запускаем разгортку..."
./corpus_build/deploy-cloudformation.sh ${ENVIRONMENT} 
# Verti Converter Lambda Function

Гэта AWS Lambda функцыя для канвэртацыі файлаў .verti у .vert фармат.

## Патрабаванні

- AWS CLI усталяваны і наладжаны
- Docker усталяваны
- AWS credentials наладжаны (`aws configure`)
- Даступ да AWS аккаўнта з дазволамі для:
  - ECR (Elastic Container Registry)
  - Lambda
  - IAM
  - S3
  - CloudFormation (калі выкарыстоўваеце CloudFormation)

## Аўтарызацыя

```bash
# Наладжванне profile
aws configure --profile my-profile

# Выкарыстанне profile
export AWS_PROFILE=my-profile
./verti_conversion/deploy-cloudformation.sh
```


## Разгортка

### Сістэма асяроддзяў

Сістэма падтрымлівае два асяроддзі:
- **dev** - дэвэлапэрскае асяроддзе (па змаўчанні)
- **prod** - прадукцыйнае асяроддзе

#### Канфігурацыя асяроддзяў

| Асяроддзе | Стэк | ECR Repository | Input Bucket | Output Bucket |
|-----------|------|----------------|--------------|---------------|
| dev | `verti-converter-dev` | `ibm-verti-converter-dev` | `ibm-editor-dev` | `ibm-vert-dev` |
| prod | `verti-converter-prod` | `ibm-verti-converter-prod` | `ibm-editor` | `ibm-vert` |

### 1. Разгортка з CloudFormation (рэкамендуецца для прадукцыйнага асяроддзя)

```bash
# Разгортка для dev асяроддзя (па змаўчанні)
./verti_conversion/deploy-cloudformation.sh

# Або яўна
./verti_conversion/deploy-cloudformation.sh dev

# Разгортка для prod асяроддзя
./verti_conversion/deploy-cloudformation.sh prod
```

### 2. Хуткі дэплоймэнт коду (толькі для змен коду функцыі)

```bash
# Хуткі дэплоймэнт для dev асяроддзя
./verti_conversion/quick-deploy.sh dev

# Хуткі дэплоймэнт для prod асяроддзя
./verti_conversion/quick-deploy.sh prod
```

**Калі выкарыстоўваць хуткі дэплоймэнт:**
- ✅ Змянілі код функцыі (`verti_conversion.py`)
- ✅ Змянілі залежнасці (`requirements.txt`)
- ✅ Змянілі Dockerfile

**Калі выкарыстоўваць поўны дэплоймэнт:**
- ❌ Змянілі CloudFormation template (`template.yaml`)
- ❌ Змянілі IAM permissions
- ❌ Змянілі налады функцыі (timeout, memory, environment variables)
- ❌ Змянілі EventBridge schedule

### 3. Ачыстка і перазапуск (калі стэк у ROLLBACK_COMPLETE стане)

```bash
# Ачыстка і разгортка для dev асяроддзя
./verti_conversion/cleanup-and-deploy.sh

# Ачыстка і разгортка для prod асяроддзя
./verti_conversion/cleanup-and-deploy.sh prod
```

## Канфігурацыя

Перад разгорткай пераканайцеся, што ў вас ёсць:

### Для dev асяроддзя:
- S3 bucket `ibm-editor-dev` з файламі .verti
- S3 bucket `ibm-vert-dev` для вываду файлаў .vert

### Для prod асяроддзя:
- S3 bucket `ibm-editor` з файламі .verti
- S3 bucket `ibm-vert` для вываду файлаў .vert

## Зменныя асяроддзя

Функцыя выкарыстоўвае наступныя зменныя асяроддзя:

- `INPUT_BUCKET` - bucket з файламі .verti
- `OUTPUT_BUCKET` - bucket для вываду файлаў .vert
- `LOG_LEVEL` - узровень логавання (па змаўчанні: INFO)

## Тэставаньне

### Лякальнае тэставаньне

```bash
cd verti_conversion
python test_local.py
```

## Структура файлаў

```
verti_conversion/
├── verti_conversion.py        # Асноўны код Lambda функцыі
├── requirements.txt            # Залежнасці Python
├── Dockerfile                  # Docker канфігурацыя
├── deploy-cloudformation.sh    # Скрыпт разгорткі з CloudFormation
├── quick-deploy.sh            # Скрыпт хуткага дэплоймэнту коду
├── cleanup-and-deploy.sh      # Скрыпт ачысткі і перазапуску
├── template.yaml               # CloudFormation template
├── test_local.py              # Скрыпт лакальнага тэставання
└── README.md                  # Гэты файл
```

## Маніторынг

### CloudWatch Logs

Функцыя запісвае логі ў CloudWatch.

### Маніторынг S3

Функцыя стварае файл `_info.txt` у output bucket з інфармацыяй пра апошняе абнаўленне.

## Абнаўленне

### Хуткае абнаўленне коду (рэкамендуецца для змен коду)
```bash
# Абнаўленне dev асяроддзя
./verti_conversion/quick-deploy.sh dev

# Абнаўленне prod асяроддзя
./verti_conversion/quick-deploy.sh prod
```

### Поўнае абнаўленне (для змен інфраструктуры)
```bash
# Абнаўленне dev асяроддзя
./verti_conversion/deploy-cloudformation.sh dev

# Абнаўленне prod асяроддзя
./verti_conversion/deploy-cloudformation.sh prod
```

## Выдаленне

### Для CloudFormation разгорткі:
```bash
# Выдаленне dev асяроддзя
aws cloudformation delete-stack --stack-name verti-converter-dev

# Выдаленне prod асяроддзя
aws cloudformation delete-stack --stack-name verti-converter-prod
```

## Праблемы і рашэнні

### Памылка "ROLLBACK_COMPLETE state"
Калі стэк у ROLLBACK_COMPLETE стане, выкарыстоўвайце:
```bash
# Для dev асяроддзя
./verti_conversion/cleanup-and-deploy.sh dev

# Для prod асяроддзя
./verti_conversion/cleanup-and-deploy.sh prod
```

### Памылка "No such file or directory"
Пераканайцеся, што ўсе файлы знаходзяцца ў папцы `verti_conversion/`

### Памылка "Permission denied"
Праверце AWS credentials і дазволы

### Памылка "Bucket does not exist"
Стварыце неабходныя S3 buckets перад разгорткай

### Функцыя не запускаецца
Праверце CloudWatch Logs для дэталяў памылак
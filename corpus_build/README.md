# Corpus Build Lambda Function

Гэта AWS Lambda функцыя для запуску зборкі корпусу праз AWS CodeBuild. Функцыя счапляе ўсе .vert файлы ў адзін і запускае CodeBuild праект для зборкі Docker image.

## Апісаньне працэсу

1. **Трыгер**: Запускаецца штоночы, правярае ці ёсьць абноўленыя vert файлы ў прараўнаньні з часам апошняга білду
2. **Сканаваньне**: Знаходзіць усе .vert файлы ў input bucket
3. **Счапленьне**: Аб'ядноўвае ўсе .vert файлы ў адзін `all.vert` з выкарыстаньнем S3 Multipart Upload
4. **CodeBuild**: Запускае CodeBuild праект для зборкі Docker image
5. **Зборка**: CodeBuild сцьягвае NoSketch Engine рэпазіторый і зьбірае Docker image
6. **Пуш**: CodeBuild выпіхвае image ў registry.digitalocean.com/bytest

## Патрабаваньні

- AWS CLI усталяваны і наладжаны
- Docker усталяваны
- AWS credentials наладжаны (`aws configure`)
- Доступ да AWS аккаўнта з дазволамі для:
  - ECR (Elastic Container Registry)
  - Lambda
  - IAM
  - S3
  - CloudFormation
  - CodeBuild
  якія менавіта дазволы патрэбныя, я ня змог разабрацца і проста дазволіў поўны доступ да гэтых сэрвісаў.
- Доступ да DigitalOcean Container Registry

## Аўтарызацыя

```bash
# Налада просфілю
aws configure --profile my-profile

# Выкарыстаньне профілю
export AWS_PROFILE=my-profile
./corpus_build/deploy-cloudformation.sh
```

## Разгортка

### Архітэктура

**CodeBuild + Lambda** - Lambda запускае CodeBuild праект для зборкі Docker image

### Асяроддзі

Сістэма падтрымлівае два асяроддзі:
- **dev** - дэвэлапэрскае асяроддзе (па змоўчанні)
- **prod** - прод

#### Канфігурацыя асяроддзяў

| Асяроддзе | Стэк                | ECR Repository          | Input Bucket   | CodeBuild Project   |
|-----------|---------------------|-------------------------|----------------|---------------------|
| dev       | `corpus-build-dev`  | `ibm-corpus-build-dev`  | `ibm-vert-dev` | `corpus-build-dev`  |
| prod      | `corpus-build-prod` | `ibm-corpus-build-prod` | `ibm-vert`     | `corpus-build-prod` |

### Разгортка з CloudFormation

```bash
# Разгортка для dev асяроддзя (па змаўчанні)
./corpus_build/deploy-cloudformation.sh

# Або яўна
./corpus_build/deploy-cloudformation.sh dev

# Разгортка для prod асяроддзя
./corpus_build/deploy-cloudformation.sh prod
```

### Хуткі дэплоймэнт коду (толькі для зьмен коду функцыі)

```bash
# Хуткі дэплоймэнт для dev асяроддзя
./corpus_build/quick-deploy.sh dev

# Хуткі дэплоймэнт для prod асяроддзя
./corpus_build/quick-deploy.sh prod
```

**Калі выкарыстоўваць хуткі дэплоймэнт:**
- ✅ Зьмянілі код функцыі (`corpus_build.py`)
- ✅ Зьмянілі залежнасьці (`requirements.txt`)
- ✅ Зьмянілі Dockerfile

**Калі выкарыстоўваць поўны дэплоймэнт:**
- ❌ Зьмянілі CloudFormation template (`template.yaml`)
- ❌ Зьмянілі IAM permissions
- ❌ Зьмянілі налады функцыі (timeout, memory, environment variables)
- ❌ Зьмянілі EventBridge schedule

### 3. Ачыстка і перазапуск (калі стэк у ROLLBACK_COMPLETE стане)

```bash
# Ачыстка і разгортка для dev асяроддзя
./corpus_build/cleanup-and-deploy.sh

# Ачыстка і разгортка для prod асяроддзя
./corpus_build/cleanup-and-deploy.sh prod
```


## Канфігурацыя

Перад разгорткай пераканайцеся, што ў вас ёсць:

### Для dev асяроддзя:
- S3 bucket `ibm-vert-dev` з файламі .vert
- Файл `bytest` (канфігурацыя NoSke індэксу) у bucket `ibm-vert-dev`

### Для prod асяроддзя:
- S3 bucket `ibm-vert` з файламі .vert
- Файл `bytest` (канфігурацыя NoSke індэксу) у bucket `ibm-vert`

## Пераменныя асяроддзя

Функцыя выкарыстоўвае наступныя пераменныя асяроддзя:

- `ENVIRONMENT` - асяроддзе (dev або prod)
- `INPUT_BUCKET` - bucket з файламі .vert
- `LOG_LEVEL` - узровень логавання (па змаўчанні: INFO)

## Лёгіка запуску

### Умовы для запуску зборкі:
Апошні пасьляховы білд быў раней за час апошняй канвэртацыі ў vert файлы (бярэцца з _info.json у кошыку s3)


## Структура corpora

Функцыя стварае наступную структуру:

```
corpora/
├── registry/
│   └── bytest          # Сьцягнуты з S3
└── bytest/
    └── all.vert        # Сабраны з усіх файл
```


## Структура файлаў

```
corpus_build/
├── corpus_build.py          # Асноўны код Lambda функцыі
├── requirements.txt         # Залежнасці Python
├── Dockerfile               # Docker канфігурацыя для лямбды
├── deploy-cloudformation.sh # Скрыпт разгорткі з CloudFormation
├── quick-deploy.sh          # Скрыпт хуткага дэплоймэнту коду
├── cleanup-and-deploy.sh    # Скрыпт ачысткі і перазапуску
├── template.yaml            # CloudFormation template
└── README.md                # Гэты файл
```

## Выдаленьне

### Для CloudFormation разгорткі:
```bash
# Выдаленьне dev асяроддзя
aws cloudformation delete-stack --stack-name corpus-build-dev

# Выдаленьне prod асяроддзя
aws cloudformation delete-stack --stack-name corpus-build-prod
```


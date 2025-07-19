# POS Tagger з выкарыстаннем розных LLM

Праект для морфалагічнай разметкі тэкстаў з выкарыстаннем розных моўных мадэляў (Claude, ChatGPT, Gemini) для разьвязаньня аманіміі.

## Патрабаванні

- Python 3.9 або навейшы
- Poetry (інструмент для кіравання залежнасцямі)

## Усталяванне

1. Кланіруйце рэпазіторый:
```bash
git clone <url-рэпазіторыя>
cd <назва-праекта>
```

2. Усталюйце Poetry (калі яшчэ не ўсталявана):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Усталюйце залежнасці праекта:
```bash
poetry install
```

## Наладка

1. Стварыце файл `.env` у каранёвай дырэкторыі
2. Дадайце свае API ключы:
```
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
PROVIDER_TYPE={gemini|anthropic}
```

## Распрацоўка

### Запуск праекта

Запусціць праект можна наступным чынам:

#### Інтэрактыўны пошук па граматычнай базе:
```bash
poetry run python -m automations.interactive_search_cli grammar-base
```
Па форме слова знаходзіць дзе ў граматычнай базе такая форма сустракаецца. Не патрабуе ШІ.

#### Разьметка файла з выкарыстаньнем ШІ
```
poetry run python automations/analyze_cli.py -b ./grammar-base/ -i your_file.txt -o output_file.vert
```
Канвэртуе звычайны тэкставы файл у vert файл з разьметкаю. Патрэбуе канфігурацыі api ключа ад google ці anthropic.

### Інструменты для распрацоўкі

У праекце наладжаны наступныя інструменты:

- **black**: фарматаванне кода
  ```bash
  poetry run black automations/
  ```

- **flake8**: праверка стылю кода
  ```bash
  poetry run flake8 automations/
  ```

- **mypy**: статычная тыпізацыя
  ```bash
  poetry run mypy automations
  ```

- **pytest**: запуск тэстаў
  ```bash
  poetry run pytest
  ```

## Дадаванне новых залежнасцяў

Каб дадаць новую залежнасць:
```bash
poetry add <назва-пакета>
```

Для залежнасцяў распрацоўкі:
```bash
poetry add --group dev <назва-пакета>
```

## Структура праекта

```
├── automations/              # Асноўны код праекта
├── verti_conversion/         # AWS Lambda для канвэртацыі .verti файлаў
├── corpus_build/             # AWS Lambda для зборкі корпуса
├── grammar-base/             # Граматычная база даных
├── tests/                    # Тэсты
└── README.md                 # Гэты файл
```

## AWS Lambda функцыі

### Verti Converter Lambda

Функцыя для канвэртацыі файлаў .verti у .vert фармат. Знаходзіцца ў папцы `verti_conversion/`.

Для разгорткі глядзіце [README файл verti_conversion](./verti_conversion/README.md).

### Corpus Build Lambda

Функцыя для запуску зборкі корпуса праз AWS CodeBuild. Канкатэнуе .vert файлы і запускае CodeBuild праект для зборкі Docker image. Знаходзіцца ў папцы `corpus_build/`.

Для разгорткі глядзіце [README файл corpus_build](./corpus_build/README.md).

### Пайплайн працэсу

1. **Verti Conversion**: Канвэртуе .verti файлы ў .vert фармат
2. **Corpus Build**: Запускаецца пасля паспяховага завершэння verti_conversion
   - Сканавае ўсе .vert файлы
   - Канкатэнуе іх у all.vert
   - Запускае CodeBuild праект
   - CodeBuild саборвае Docker image з NoSketch Engine
   - CodeBuild запушвае ў registry.digitalocean.com/bytest

## Выкарыстанне

Інструкцыі па выкарыстанні будуць дададзены пазней. 
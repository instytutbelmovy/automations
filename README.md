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
poetry run python automations/interactive_search_cli.py grammar-base/
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

## Выкарыстанне

Інструкцыі па выкарыстанні будуць дададзены пазней. 
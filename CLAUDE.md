# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language conventions

Code comments, docstrings, log messages, CLI help text and commit messages are in Belarusian (in the classical/taraškievica orthography). Follow that when editing — do not translate existing Belarusian text to English. Identifiers are English.

## Commands

Poetry-managed; run everything through `poetry run` from the repo root.

```bash
poetry install
poetry run pytest                              # all tests
poetry run pytest tests/test_tokenizer.py      # one file
poetry run pytest tests/test_tokenizer.py::TestTokenizer::test_simple_sentence   # one test
poetry run black automations/                  # line-length 200 (configured in pyproject.toml)
poetry run flake8 automations/
poetry run mypy automations
```

Tests use `unittest.TestCase` classes but are run by pytest, and import via the `automations.` package path, so they only work from the repo root.

### CLI entry points

```bash
# verti utility (also installed as the `verti` script)
poetry run python -m automations.verti_cli convert 'books/*.epub' out/        # epub|txt|docx|pdf -> .verti
poetry run python -m automations.verti_cli fog in.verti out.verti ./grammar-base/   # fill unambiguous grammar
poetry run python -m automations.verti_cli tovert in.verti out.vert          # .verti -> .vert (NoSketch format)
poetry run python -m automations.verti_cli to_pos in.verti out.txt           # word/lemma/POS-letter columns
poetry run python -m automations.verti_cli to_text in.verti out.txt          # plain text, one paragraph per line
poetry run python -m automations.verti_cli fill-meta '*.verti' meta.xlsx [--overwrite-meta]

# LLM-assisted disambiguation (needs API keys)
poetry run python -m automations.analyze_cli -b ./grammar-base/ -i file.txt -o out.vert

# grammar base lookup, no AI
poetry run python -m automations.interactive_search_cli grammar-base
```

Every input argument accepts a glob; with multiple matches the output argument must be a directory. Output extensions per command live in `OUTPUT_EXTENSIONS` in [automations/verti_cli.py](automations/verti_cli.py#L22).

`.env` at the repo root: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `PROVIDER_TYPE={gemini|anthropic}`, `LOG_LEVEL`. `verti_conversion/.env` holds `INPUT_BUCKET`/`OUTPUT_BUCKET`/`AWS_PROFILE` for local Lambda runs.

## Architecture

### The two file formats

Everything revolves around two line-oriented, pseudo-XML formats read and written by [automations/vert_io.py](automations/vert_io.py):

- **`.verti`** — the internal working format. One token per line, tab-separated columns: `text`, `ParadigmFormId`, `lemma`, `LinguisticTag`, JSON comment, JSON metadata. Compact codes, editable by humans, carries `id`/`concurrency_stamp` attributes on `<p>`/`<s>` used by the external editor app.
- **`.vert`** — the output fed to NoSketch Engine. Lemma is unstressed, and the compact tag is expanded into ~29 tab-separated human-readable Belarusian columns by `LinguisticTag.to_expanded_string()`.

Structural markers in both: `<doc …>` header with corpus metadata, `<p>`, `<s>`, `<lb/>` (line break), `<g/>` (glue to previous token, i.e. no space). `PUNCT` in the second column marks punctuation.

`.verti` → `.vert` is lossy and one-way. If you change the tag vocabulary you must touch both `to_expanded_string()` (vert column layout) and the `_decode_*_form_tag` methods in `grammar_db.py` (human-readable descriptions used for LLM prompts) — they encode the same linguistics in two places.

### Ingest pipeline

`DocReader` subclass (txt/docx/pdf/epub) → `SourceDocument` (plain paragraph strings + metadata) → `DocParser` → `Tokenizer` (chars → `Token`s, handles apostrophes, dashes, stress marks, sentence separators) → `Sentencer` (`Token`s → `SentenceItem`s grouped into sentences, computes `glue_next`) → `CorpusDocument` → `VertIO.write_verti`.

To support a new input format, add a `DocReader` subclass and register it in `convert_to_verti` in verti_cli.py.

### Tags and the grammar base

- `grammar-base/*.xml` is the Belarusian grammar database (one file per part of speech, `Paradigm > Variant > Form`). `GrammarDB.load_directory` indexes every word form in memory — this takes a while, so load it once and reuse (see the `fog` command).
- `ParadigmFormId` (`<paradigmId><variant>.<formTag>`) points into that XML; `LinguisticTag` (`paradigmTag|formTag`) is the grammatical description. Both support `intersect_with` / `union_with`: intersection collapses ambiguity across candidate readings into a partial tag (`.` marks unknown positions), union merges newly inferred info into what a human already entered.
- `GrammarDB.infer_grammar_info` returns only what all candidate readings agree on — so unambiguous words get fully resolved and ambiguous ones get a partial tag.
- `Normalizer` has three deliberately different normalization strengths (tokenization, grammar-base light = keeps case/stress, grammar-base aggressive = lowercase and `ў`→`у`). Picking the wrong one silently breaks lookups.

### LLM disambiguation

`MorphologicalAnalyzer` + a `BaseProvider` implementation (`AnthropicProvider`, `GeminiProvider`) resolve homonymy the grammar base cannot. This path is older and separate from the verti pipeline: it does its own regex tokenization and writes vert directly, rather than going through `Tokenizer`/`VertIO`. Note `automations/base_provider.py` uses a non-relative `from linguistic_bits import …`, so `analyze_cli` is currently broken on import — fix that before relying on this path.

## AWS pipeline

Nightly, two Lambdas (both container images, both deployed per environment `dev`/`prod`) plus CodeBuild:

1. **verti_conversion** (cron 02:37 UTC) — lists `.verti` in the editor bucket newer than `_info.json`'s `lastModified`, converts each with `VertIO`, writes `.vert` to the vert bucket with the document's `corpus` value as **base64-encoded** S3 object metadata (S3 metadata is ASCII-only), then advances `_info.json`.
2. **corpus_build** (cron 04:43 UTC) — builds only if `_info.json`'s `processed` is newer than the last successful CodeBuild; groups `.vert` files by that `corpus` metadata, concatenates each group into `concatenated/<lacinka>/<lacinka>.vert` via S3 multipart upload (never buffering in Lambda memory), generates a NoSketch registry `.conf` per corpus from `template.conf`, plus an "Усе тэксты" corpus over all files; then starts CodeBuild.
3. **CodeBuild** (buildspec inlined in `corpus_build/template.yaml`) — clones `instytutbelmovy/NoSketch-Engine-Docker` branch `ibm-build`, syncs `concatenated/` into `corpora/`, writes `static/version.json` (noske commit + build timestamp, served at `/version.json`), builds and pushes to ECR `instytutbelmovy-noske-{env}` as `latest` + timestamp tag.
4. **Hetzner VPS** pulls from ECR on a systemd timer — AWS has no access to the VPS, only a read-only ECR IAM user for it. See [corpus_build/vps/README.md](corpus_build/vps/README.md).

The Dockerfiles build from the **repo root** (`COPY automations …`), so verti_conversion shares the real `VertIO` code with the CLI. corpus_build does not — it never parses vert content, only shuffles S3 objects.

Deploy scripts take `dev`|`prod` (default `dev`) and must be run from the repo root:

```bash
./verti_conversion/quick-deploy.sh dev          # code/deps/Dockerfile changes only
./verti_conversion/deploy-cloudformation.sh dev  # template.yaml, IAM, schedule, function settings
./verti_conversion/cleanup-and-deploy.sh dev     # stack stuck in ROLLBACK_COMPLETE
```

Region is `eu-central-1`. quick-deploy bakes the current git hash/branch/date into `git_info.json` inside the image, which verti_conversion returns in its response — use it to check which code version is live. `python verti_conversion/test_local.py` invokes the handler locally against real S3 buckets.

## marketingResApp

Extract company emails from an Excel file.

You can run it in two ways:
- **Simple mode (recommended)**: drop an `.xlsx` into `input/` → get output in `output/`
- **Explicit mode**: pass `--in` and `--out`

## One-time setup

From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Optional: configure SerpAPI key (recommended)

SerpAPI helps when websites block crawling or don’t show emails directly.

```bash
cp .env.example .env
```

Open `.env` and set:

```bash
SERPAPI_KEY="paste_your_key_here"
```

Then load it into your shell:

```bash
set -a
source .env
set +a
```

## Put your Excel in `input/`

Copy your `.xlsx` file into:

- `input/`

Notes:
- the tool will pick the **newest** `.xlsx` in `input/`
- ignore files like `~$something.xlsx` (Excel temp files)

## Run (simple mode)

```bash
source .venv/bin/activate
python -m project.cli excel \
  --company-col "title" \
  --url-col "website" \
  --use-search
```

## Get your output

Your output Excel will be created in:

- `output/`

Filename format:
- `output/<input_stem>_emails_output.xlsx`

## Explicit mode (optional)

Use this if you want to specify exact paths:

```bash
python -m project.cli excel \
  --in "/path/to/input.xlsx" \
  --out "/path/to/output.xlsx" \
  --company-col "title" \
  --url-col "website" \
  --use-search
```

## Output columns

The tool appends these columns to the Excel:
- **`normalized_url`**: normalized website URL used for crawling
- **`emails`**: `; ` separated emails
- **`email_count`**: number of kept emails
- **`source_notes`**: crawl/search notes + `filtered=X/Y`

## Troubleshooting

- **0 emails for many rows**: common causes are blank `website` cells, website blocking (403/429), emails only in contact forms/JavaScript.
- **Search fallback returns nothing**: ensure `SERPAPI_KEY` is loaded and `--use-search` is set.
- **Too slow / too fast**: tune `--max-pages-per-site` and `--timeout-s`.

## Single URL mode

```bash
python -m project.cli url --url https://example.com --company "Example Inc"
```


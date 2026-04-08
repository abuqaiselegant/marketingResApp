from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from project.excel_io import read_companies_from_excel, write_results_to_excel
from project.models import CompanyEmailResult
from project.pipeline import extract_emails_for_company


app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


def _project_dir() -> Path:
    # project/cli.py -> repo root
    return Path(__file__).resolve().parent.parent


def _default_input_dir() -> Path:
    return _project_dir() / "input"


def _default_output_dir() -> Path:
    return _project_dir() / "output"


def _pick_latest_xlsx(input_dir: Path) -> Path:
    if not input_dir.exists():
        raise typer.BadParameter(f"Input folder not found: {input_dir}")
    files = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".xlsx" and not p.name.startswith("~$")]
    if not files:
        raise typer.BadParameter(f"No .xlsx files found in: {input_dir}")
    return max(files, key=lambda p: p.stat().st_mtime)


@app.command("excel")
def excel_cmd(
    in_path: Optional[Path] = typer.Option(None, "--in", dir_okay=False, readable=True),
    out_path: Optional[Path] = typer.Option(None, "--out", dir_okay=False),
    company_col: Optional[str] = typer.Option(None, "--company-col"),
    url_col: Optional[str] = typer.Option(None, "--url-col"),
    max_pages_per_site: int = typer.Option(8, "--max-pages-per-site", min=1, max=50),
    timeout_s: float = typer.Option(15.0, "--timeout-s", min=2.0, max=60.0),
    use_search: bool = typer.Option(False, "--use-search"),
    search_provider: str = typer.Option("serpapi", "--search-provider"),
    serpapi_key: Optional[str] = typer.Option(None, "--serpapi-key", envvar="SERPAPI_KEY"),
):
    input_dir = _default_input_dir()
    output_dir = _default_output_dir()
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_in = in_path or _pick_latest_xlsx(input_dir)
    if not resolved_in.exists():
        raise typer.BadParameter(f"Input file not found: {resolved_in}")

    resolved_out = out_path
    if resolved_out is None:
        stem = resolved_in.stem
        resolved_out = output_dir / f"{stem}_emails_output.xlsx"

    rows = read_companies_from_excel(
        resolved_in,
        company_col=company_col,
        url_col=url_col,
    )

    results = []
    for row in rows:
        r = extract_emails_for_company(
            company=row.company,
            url=row.url,
            max_pages=max_pages_per_site,
            timeout_s=timeout_s,
            use_search=use_search,
            search_provider=search_provider,
            serpapi_key=serpapi_key,
        )
        results.append(
            CompanyEmailResult(
                row_index=row.row_index,
                company=r.company,
                input_url=r.input_url,
                normalized_url=r.normalized_url,
                emails=r.emails,
                source_notes=r.source_notes,
            )
        )

    write_results_to_excel(in_path=resolved_in, out_path=resolved_out, results=results)
    console.print(f"[green]Read:[/green]  {resolved_in}")
    console.print(f"[green]Wrote:[/green] {resolved_out}")


@app.command("url")
def url_cmd(
    url: str = typer.Option(..., "--url"),
    company: str = typer.Option(""),
    max_pages_per_site: int = typer.Option(8, "--max-pages-per-site", min=1, max=50),
    timeout_s: float = typer.Option(15.0, "--timeout-s", min=2.0, max=60.0),
    use_search: bool = typer.Option(False, "--use-search"),
    search_provider: str = typer.Option("serpapi", "--search-provider"),
    serpapi_key: Optional[str] = typer.Option(None, "--serpapi-key", envvar="SERPAPI_KEY"),
):
    result = extract_emails_for_company(
        company=company,
        url=url,
        max_pages=max_pages_per_site,
        timeout_s=timeout_s,
        use_search=use_search,
        search_provider=search_provider,
        serpapi_key=serpapi_key,
    )
    console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    app()


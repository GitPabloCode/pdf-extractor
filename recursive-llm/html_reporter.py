"""
html_reporter.py — Genera un report HTML con link cliccabili al viewer dinamico.

Ogni citazione [¶N] nella risposta diventa un link che apre
viewer.html#¶N, mostrando la pagina con la bbox gialla della citazione.
"""

import os
import re
from pathlib import Path
from typing import Any


def _build_prefix_map(doc_dirs: list[str]) -> dict[str, str]:
    """Costruisce mappa: prefix (es. '35') → percorso assoluto doc_dir."""
    prefix_map: dict[str, str] = {}
    for d in doc_dirs:
        name = Path(d).name
        prefix = name.replace("subset", "")
        prefix_map[prefix] = str(Path(d).resolve())
    return prefix_map


def _linkify_anchors(text: str, prefix_map: dict[str, str], html_dir: str) -> str:
    """Sostituisce [¶35-1] o [¶1] con link al viewer.html del subset corretto."""

    def replacer(m: re.Match) -> str:
        prefix = m.group(1)
        num = m.group(2)
        if prefix and prefix in prefix_map:
            viewer_abs = os.path.join(prefix_map[prefix], "viewer.html")
            display_anchor = f"¶{prefix}-{num}"
        else:
            # Fallback: usa il primo doc_dir disponibile
            first_dir = next(iter(prefix_map.values()), ".")
            viewer_abs = os.path.join(first_dir, "viewer.html")
            display_anchor = f"¶{num}"
        viewer_rel = os.path.relpath(viewer_abs, html_dir)
        return (
            f'<a href="{viewer_rel}#{num}" '
            f'title="Apri viewer con bbox gialla per {display_anchor}" '
            f'target="_blank" class="citation">[{display_anchor}]</a>'
        )

    return re.sub(r"\[¶(?:(\d+)-)?(\d+)\]", replacer, text)


def generate_html_report(
    results: list[dict[str, Any]],
    doc_dirs,
    output_path: str,
    model: str = "",
    title: str = "Report Q&A con Fonti",
) -> Path:
    """Genera un report HTML con risposte e link cliccabili alle fonti.

    Args:
        results: lista di {
            question, expected_answer, expected_page, answer, sources
        }
        sources è lista di {anchor, page, type, content, doc_dir}
        doc_dirs: stringa o lista di cartelle che contengono viewer.html
        output_path: dove salvare l'HTML
        model: nome del modello usato
        title: titolo del report
    """
    if isinstance(doc_dirs, str):
        doc_dirs = [doc_dirs]
    prefix_map = _build_prefix_map(doc_dirs)
    html_dir = str(Path(output_path).parent.resolve())

    rows_html: list[str] = []

    tot_prompt = 0
    tot_completion = 0
    tot_total = 0

    for i, r in enumerate(results, 1):
        question = r.get("question", "")
        expected_answer = r.get("expected_answer") or ""
        expected_page = r.get("expected_page") or ""
        answer = r.get("answer", "")
        sources: list[dict] = r.get("sources", [])
        tokens: dict = r.get("tokens", {})

        pt = tokens.get("prompt_tokens", 0) or 0
        ct = tokens.get("completion_tokens", 0) or 0
        tt = tokens.get("total_tokens", 0) or 0
        tot_prompt += pt
        tot_completion += ct
        tot_total += tt

        answer_linked = _linkify_anchors(answer, prefix_map, html_dir)

        # Colonna Fonti
        if sources:
            fonti_parts = []
            for s in sources:
                a = s["anchor"]
                p = s["page"]
                src_doc_dir = s.get("doc_dir", doc_dirs[0])
                viewer_abs = os.path.join(str(Path(src_doc_dir).resolve()), "viewer.html")
                viewer_rel = os.path.relpath(viewer_abs, html_dir)
                num = a.lstrip("¶")
                if "-" in num:
                    num = num.split("-", 1)[1]
                fonti_parts.append(
                    f'<a href="{viewer_rel}#{num}" target="_blank" '
                    f'class="source-link" title="Apri viewer per {a}">{a}</a>'
                    f'<span class="source-page">(p. {p})</span>'
                )
            fonti_html = " ".join(fonti_parts)
        else:
            fonti_html = '<span class="no-source">—</span>'

        token_html = (
            f'<span class="token-info" title="prompt: {pt} · completion: {ct}">'
            f'{tt}</span>'
        ) if tt else '<span class="no-source">—</span>'

        rows_html.append(f"""
            <tr>
                <td class="col-num">{i}</td>
                <td class="col-question">{question}</td>
                <td class="col-gt">{expected_answer}</td>
                <td class="col-gt-page">{expected_page}</td>
                <td class="col-answer">{answer_linked}</td>
                <td class="col-sources">{fonti_html}</td>
                <td class="col-tokens">{token_html}</td>
            </tr>
        """)

    style = """
    <style>
        :root {
            --bg: #f5f5f5;
            --card-bg: #ffffff;
            --text: #333333;
            --muted: #777777;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --border: #e5e5e5;
            --header-bg: #1e293b;
            --header-text: #ffffff;
            --gt-bg: #f0fdf4;
            --num-color: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            margin: 0; padding: 24px;
            background: var(--bg); color: var(--text);
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { text-align: center; color: #1e293b; margin-bottom: 8px; font-size: 1.5em; }
        .meta {
            text-align: center; color: var(--muted); margin-bottom: 24px;
            font-size: 0.9em;
        }
        .table-wrapper {
            background: var(--card-bg); border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06); overflow: hidden;
        }
        table {
            width: 100%; border-collapse: collapse; font-size: 0.92em;
            table-layout: fixed;
        }
        th, td {
            padding: 14px 16px; border-bottom: 1px solid var(--border);
            vertical-align: top; word-wrap: break-word;
        }
        th {
            background: var(--header-bg); color: var(--header-text);
            font-weight: 600; font-size: 0.85em; text-transform: uppercase;
            letter-spacing: 0.4px; text-align: left; position: sticky; top: 0; z-index: 1;
        }
        th.col-num      { width: 3%;  text-align: center; }
        th.col-question { width: 16%; }
        th.col-gt       { width: 18%; background: #166534; }
        th.col-gt-page  { width: 4%;  text-align: center; background: #166534; }
        th.col-answer   { width: 34%; background: #0f3b5c; }
        th.col-sources  { width: 16%; }
        th.col-tokens   { width: 6%;  text-align: center; }

        td.col-num { text-align: center; color: var(--num-color); font-weight: 600; }
        td.col-gt { background: var(--gt-bg); font-size: 0.88em; }
        td.col-gt-page { background: var(--gt-bg); text-align: center; font-weight: 600; }
        td.col-answer { line-height: 1.7; }

        tr:hover td { background: #fafbfc; }
        tr:hover td.col-gt { background: #e6f7ec; }

        a.citation {
            color: var(--accent); text-decoration: none; font-weight: 600;
            font-size: 0.85em; padding: 1px 4px; border-radius: 3px;
            background: #eff6ff; white-space: nowrap;
            transition: background 0.15s, color 0.15s;
        }
        a.citation:hover { background: #dbeafe; color: var(--accent-hover); }

        a.source-link {
            display: inline-block; color: var(--accent); text-decoration: none;
            font-weight: 600; padding: 2px 6px; border-radius: 3px;
            background: #eff6ff; margin: 2px 1px; font-size: 0.9em;
            transition: background 0.15s;
        }
        a.source-link:hover { background: #dbeafe; }
        .source-page { font-size: 0.8em; color: var(--muted); margin-left: 2px; }
        .no-source { color: var(--muted); font-style: italic; }

        td.col-tokens { text-align: center; }
        .token-info {
            display: inline-block; font-weight: 600; font-size: 0.85em;
            color: #6366f1; background: #eef2ff; padding: 2px 8px;
            border-radius: 4px; cursor: default;
        }
        .token-total {
            color: #d97706; background: #fffbeb; font-size: 0.95em;
        }
        .totals-row td {
            background: #f8fafc; border-top: 2px solid #94a3b8;
        }

        td.col-answer p { margin-bottom: 8px; }
        td.col-answer ul, td.col-answer ol { margin: 6px 0 6px 20px; }
        td.col-answer li { margin-bottom: 4px; }
        td.col-answer code { background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 0.9em; }
        td.col-answer pre { background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.85em; }
        td.col-answer strong { font-weight: 600; color: #1e293b; }

        @media (max-width: 1024px) {
            table { font-size: 0.82em; }
            th, td { padding: 10px 8px; }
        }
    </style>
    """

    model_info = f"Modello: {model}" if model else ""

    full_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    {style}
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">
            {model_info}
            {' · ' if model_info else ''}
            {len(results)} domande · viewer con bbox gialla
        </div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th class="col-num">#</th>
                        <th class="col-question">Domanda</th>
                        <th class="col-gt">Risposta Attesa</th>
                        <th class="col-gt-page">Pag.</th>
                        <th class="col-answer">Risposta Modello</th>
                        <th class="col-sources">Fonti</th>
                        <th class="col-tokens">Token</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows_html)}
                </tbody>
                <tfoot>
                    <tr class="totals-row">
                        <td class="col-num"></td>
                        <td class="col-question"></td>
                        <td class="col-gt"></td>
                        <td class="col-gt-page"></td>
                        <td class="col-answer" style="text-align:right;font-weight:700;color:#1e293b;">
                            TOTALE ({len(results)} domande)
                        </td>
                        <td class="col-sources"></td>
                        <td class="col-tokens">
                            <span class="token-info token-total" title="prompt: {tot_prompt} · completion: {tot_completion}">
                                {tot_total}
                            </span>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            marked.use({{ breaks: true }});
            const answerCells = document.querySelectorAll('td.col-answer');
            answerCells.forEach(cell => {{
                let html = cell.innerHTML;
                const citations = [];
                html = html.replace(/<a [^>]*class="citation[^"]*"[^>]*>.*?<\\/a>/g, match => {{
                    citations.push(match);
                    return '%%CITATION' + (citations.length - 1) + '%%';
                }});
                let rendered = marked.parse(html);
                citations.forEach((cit, idx) => {{
                    rendered = rendered.replace('%%CITATION' + idx + '%%', cit);
                }});
                cell.innerHTML = rendered;
            }});
        }});
    </script>
</body>
</html>
"""

    out = Path(output_path)
    out.write_text(full_html, encoding="utf-8")
    return out

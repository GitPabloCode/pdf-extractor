#!/usr/bin/env python3
"""
convert_pdf.py - Converte un PDF in Markdown annotato, JSON citabile e PDF con bounding box.

Funzionalità:
  - Estrazione testo con layout preservato
  - Salvataggio immagini in images/ con riferimenti nel Markdown
  - Riconoscimento formule matematiche → LaTeX
  - Markdown con anchor inline [¶N] su ogni chunk citabile
  - JSON citazioni (citations.json): lookup O(1) per anchor → {page, type, content}
  - JSON ibrido completo (document_citabile.json): tutti i chunk con metadati
  - Visualizzazione bounding box per pagina unite in un unico PDF
  - Range di pagine selezionabile
  - Warning HuggingFace/transformers soppressi

Installazione:
  pip install docling pillow fpdf2
  pip install docling[easyocr]   # opzionale: PDF scansionati

Utilizzo:
  python convert_pdf.py documento.pdf
  python convert_pdf.py documento.pdf --pages 1-5
  python convert_pdf.py documento.pdf --pages 1,3,5,7
  python convert_pdf.py documento.pdf --no-bbox-pdf
  python convert_pdf.py documento.pdf --no-math --no-images
  python convert_pdf.py documento.pdf --ocr

Formato anchor nel Markdown:
  Ogni chunk citabile riceve un anchor inline [¶N] dove N è l'indice progressivo.
  Esempio testo:    "Il treno deve fermarsi entro 50m. [¶42]"
  Esempio heading:  "## 4.1.1 Rules for balises [¶15]"
  Esempio tabella:  anchor su riga separata prima della tabella: "[¶23]"

Citazione agente:
  [fonte: ¶42, page=3, type=text, file="documento.pdf"]
  → lookup in citations.json["¶42"] per recuperare content + metadati
"""

# ── Soppressione warning HuggingFace/transformers ─────────────────────────────
import os
import warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", message=".*tie_word_embeddings.*")
warnings.filterwarnings("ignore", message=".*generation_config.*")
warnings.filterwarnings("ignore", message=".*Passing.*generation-related.*")
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ─── Label → colore RGB ──────────────────────────────────────────────────────
LABEL_COLORS: dict[str, tuple[int, int, int]] = {
    "title":          (220,  50,  50),
    "section_header": (220, 130,  30),
    "text":           ( 50, 120, 220),
    "list_item":      ( 50, 180, 100),
    "table":          (160,  60, 200),
    "picture":        ( 30, 180, 200),
    "formula":        (200,  80, 160),
    "code":           (100, 140,  30),
    "caption":        (180, 140,  60),
    "footnote":       (130, 130, 130),
    "page_header":    (180,  90,  90),
    "page_footer":    (180,  90,  90),
    "key_value":      ( 90, 160, 160),
}
DEFAULT_COLOR = (100, 100, 100)

# Tipi di chunk da NON ancorare (non utili per citazione)
_NON_CITABLE_TYPES = {"picture", "page_header", "page_footer", "footnote"}
# Testi che indicano contenuto vuoto/cancellato
_SKIP_CONTENT_PATTERNS = (
    "intentionally deleted",
    "[immagine: ]",
    "[formula]",
)


def _is_citable(chunk: dict) -> bool:
    """Restituisce True se il chunk merita un anchor di citazione."""
    if chunk["type"] in _NON_CITABLE_TYPES:
        return False
    content_lower = chunk["content"].strip().lower()
    if not content_lower:
        return False
    for pat in _SKIP_CONTENT_PATTERNS:
        if content_lower == pat or content_lower.endswith(pat):
            return False
    return True


# ─── Parsing argomenti ───────────────────────────────────────────────────────

def parse_pages(spec: str | None) -> set[int] | None:
    if spec is None:
        return None
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return pages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Converte un PDF in Markdown annotato, JSON citabile e PDF con bounding box.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pdf_path", type=str, help="Percorso al file PDF da convertire")
    parser.add_argument("--output-dir", type=str, default="processed_documents",
                        help="Cartella di output (default: processed_documents)")
    parser.add_argument("--pages", type=str, default=None,
                        help="Pagine da elaborare. Es: '1-5', '1,3,7', '2-4,8'")
    parser.add_argument("--no-images",   action="store_true", help="Senza estrazione immagini")
    parser.add_argument("--no-math",     action="store_true", help="Senza riconoscimento formule")
    parser.add_argument("--no-bbox-pdf", action="store_true", help="Senza PDF bounding box")
    parser.add_argument("--ocr",         action="store_true",
                        help="Forza OCR (PDF scansionati). Richiede: pip install docling[easyocr]")
    return parser.parse_args()


def check_dependencies() -> None:
    missing = []
    for pkg, install in [("docling", "docling"), ("PIL", "pillow"), ("fpdf", "fpdf2")]:
        try:
            __import__("PIL.Image" if pkg == "PIL" else pkg)
        except ImportError:
            missing.append(install)
    if missing:
        print("❌ Pacchetti mancanti. Installa con:")
        for m in missing:
            print(f"   pip install {m}")
        sys.exit(1)


# ─── Pipeline Docling ────────────────────────────────────────────────────────

def build_pipeline_options(extract_images: bool, extract_math: bool,
                            force_ocr: bool, need_page_images: bool):
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    opts = PdfPipelineOptions()
    opts.do_table_structure = True
    opts.table_structure_options.mode = TableFormerMode.ACCURATE
    opts.generate_page_images    = need_page_images
    opts.generate_picture_images = extract_images
    opts.images_scale            = 2.0
    opts.do_formula_enrichment   = extract_math
    if force_ocr:
        try:
            from docling.datamodel.pipeline_options import EasyOcrOptions
            opts.do_ocr = True
            opts.ocr_options = EasyOcrOptions(force_full_page_ocr=True)
        except ImportError:
            print("⚠️  EasyOCR non trovato (pip install docling[easyocr]). OCR disabilitato.")
            opts.do_ocr = False
    else:
        opts.do_ocr = False
    return opts


def run_conversion(pdf_path: Path, extract_images: bool, extract_math: bool,
                   force_ocr: bool, need_page_images: bool):
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    opts = build_pipeline_options(extract_images, extract_math, force_ocr, need_page_images)
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    return converter.convert(str(pdf_path))


# ─── JSON ibrido + anchor ────────────────────────────────────────────────────

def _get_item_type(item) -> str:
    label = getattr(item, "label", None)
    if label is None:
        return type(item).__name__.lower().replace("item", "")
    return label.value if hasattr(label, "value") else str(label)


def build_chunks(doc_result, pdf_path: Path,
                 page_filter: set[int] | None,
                 image_map: dict[str, str]) -> list[dict[str, Any]]:
    """
    Costruisce la lista di chunk dal documento Docling.
    Ogni chunk ha:
      paragraph_id  – ID progressivo stile "p0042" (tutti i chunk, per compatibilità)
      anchor        – stringa "¶N" solo sui chunk citabili (None altrimenti)
      page_id       – numero pagina (1-based)
      type          – tipo elemento
      content       – contenuto Markdown
    """
    doc = doc_result.document
    chunks: list[dict[str, Any]] = []
    para_idx = 0   # progressivo globale (tutti i chunk)
    anchor_idx = 0  # progressivo solo per chunk citabili

    for item, _level in doc.iterate_items():
        # Filtra per pagina
        item_pages: set[int] = set()
        for prov in getattr(item, "prov", []):
            item_pages.add(prov.page_no)
        if page_filter and item_pages and not item_pages.intersection(page_filter):
            continue

        page_id: int | None = None
        bbox_raw: dict | None = None
        page_width: float | None = None
        page_height: float | None = None

        if hasattr(item, "prov") and item.prov:
            page_id = item.prov[0].page_no
            try:
                raw = item.prov[0].bbox
                bbox_raw = {"l": raw.l, "t": raw.t, "r": raw.r, "b": raw.b}
                if page_id is not None and page_id in doc.pages:
                    pg = doc.pages[page_id]
                    page_width = pg.size.width
                    page_height = pg.size.height
            except Exception:
                pass

        item_type = _get_item_type(item)

        # Contenuto Markdown
        try:
            from docling_core.types.doc import TableItem as TI, PictureItem as PI
            if isinstance(item, TI):
                md_content = item.export_to_markdown()
            elif isinstance(item, PI):
                self_ref = getattr(item, "self_ref", "") or ""
                img_path = image_map.get(self_ref)
                captions = [
                    ann.text for ann in getattr(item, "annotations", [])
                    if getattr(ann, "text", None)
                ]
                caption_md = " ".join(captions)
                md_content = f"![{caption_md}]({img_path})" if img_path else f"[immagine: {caption_md}]"
            else:
                raw = getattr(item, "text", "") or ""
                if item_type == "formula":
                    md_content = f"$$\n{raw}\n$$" if raw else "[formula]"
                elif item_type == "section_header":
                    lvl = getattr(item, "level", 1) or 1
                    md_content = f"{'#' * lvl} {raw}"
                elif item_type == "title":
                    md_content = f"# {raw}"
                elif item_type == "list_item":
                    md_content = f"- {raw}"
                elif item_type == "code":
                    lang = getattr(item, "code_language", "") or ""
                    md_content = f"```{lang}\n{raw}\n```"
                else:
                    md_content = raw
        except Exception:
            md_content = getattr(item, "text", "") or ""

        if not md_content.strip():
            continue

        chunk: dict[str, Any] = {
            "paragraph_id": f"p{para_idx:04d}",
            "anchor":       None,           # verrà assegnato sotto se citabile
            "page_id":      page_id,
            "type":         item_type,
            "content":      md_content,
            "bbox":         bbox_raw,
            "page_width":   page_width,
            "page_height":  page_height,
        }

        # Assegna anchor solo ai chunk citabili
        if _is_citable(chunk):
            chunk["anchor"] = f"¶{anchor_idx}"
            anchor_idx += 1

        chunks.append(chunk)
        para_idx += 1

    return chunks


def build_hybrid_json(chunks: list[dict], pdf_path: Path,
                      total_pages: int) -> dict[str, Any]:
    """JSON completo con tutti i chunk (compatibile con il formato originale)."""
    return {
        "source_file":   pdf_path.name,
        "total_pages":   total_pages,
        "total_chunks":  len(chunks),
        "citable_chunks": sum(1 for c in chunks if c["anchor"] is not None),
        "chunks":        chunks,
    }


def build_citations_index(chunks: list[dict], pdf_path: Path) -> dict[str, Any]:
    """
    Indice di citazione per lookup O(1).
    Chiave: anchor string "¶N"
    Valore: {paragraph_id, page_id, type, content}

    Uso agente:
      citations["¶42"]  →  {page_id: 3, type: "text", content: "…"}
    """
    index: dict[str, Any] = {}
    for chunk in chunks:
        if chunk["anchor"] is None:
            continue
        index[chunk["anchor"]] = {
            "paragraph_id": chunk["paragraph_id"],
            "page_id":      chunk["page_id"],
            "type":         chunk["type"],
            "content":      chunk["content"],
            "bbox":         chunk.get("bbox"),
            "page_width":   chunk.get("page_width"),
            "page_height":  chunk.get("page_height"),
        }
    return {
        "source_file":    pdf_path.name,
        "total_citable":  len(index),
        "anchor_format":  "¶N  (e.g. ¶0, ¶42, ¶255)",
        "usage":          'citations["¶42"] → {paragraph_id, page_id, type, content}',
        "citations":      index,
    }


# ─── Immagini ────────────────────────────────────────────────────────────────

def save_images(doc_result, images_dir: Path) -> dict[str, str]:
    images_dir.mkdir(parents=True, exist_ok=True)
    image_map: dict[str, str] = {}
    for idx, picture in enumerate(doc_result.document.pictures, start=1):
        try:
            pil_image = picture.get_image(doc_result)
            if pil_image is None:
                continue
            fname = f"image_{idx:04d}.png"
            pil_image.save(str(images_dir / fname), format="PNG")
            ref = getattr(picture, "self_ref", None) or str(idx)
            image_map[ref] = f"images/{fname}"
            print(f"   🖼  {fname}")
        except Exception as e:
            print(f"   ⚠️  Immagine {idx}: {e}")
    return image_map


# ─── Export Markdown con anchor inline ───────────────────────────────────────

def _inject_anchor(md_content: str, anchor: str, item_type: str) -> str:
    """
    Inserisce l'anchor [¶N] nel punto corretto in base al tipo di elemento.

    - heading  → "## Titolo [¶N]"          (anchor in fondo alla riga)
    - table    → "[¶N]\n| col |…"          (anchor su riga separata PRIMA)
    - formula  → "$$\\n…\\n$$ [¶N]"        (anchor dopo il blocco)
    - code     → "```\\n…\\n``` [¶N]"      (anchor dopo il blocco)
    - altri    → "Testo. [¶N]"             (anchor in fondo al testo)
    """
    tag = f"[{anchor}]"

    if item_type in ("section_header", "title"):
        # Prima riga = heading; anchor in coda sulla stessa riga
        lines = md_content.split("\n", 1)
        lines[0] = lines[0].rstrip() + f" {tag}"
        return "\n".join(lines)

    if item_type == "table":
        # Anchor su riga separata prima della tabella, così non rompe il parser MD
        return f"{tag}\n{md_content}"

    if item_type in ("formula", "code"):
        # Anchor sulla stessa riga dopo la chiusura del blocco
        return md_content.rstrip() + f" {tag}"

    # Default: testo, list_item, caption, key_value, ecc.
    return md_content.rstrip() + f" {tag}"


def export_markdown_with_anchors(chunks: list[dict],
                                  output_dir: Path,
                                  page_filter: set[int] | None) -> Path:
    """
    Genera il Markdown con anchor inline [¶N] su ogni chunk citabile.
    I chunk non citabili (immagini, placeholder, ecc.) vengono inclusi senza anchor.
    """
    lines: list[str] = []

    if page_filter:
        pages_str = ", ".join(str(p) for p in sorted(page_filter))
        lines.append(f"> ⚠️ Documento estratto dalle pagine: {pages_str}\n")

    current_page: int | None = None

    for chunk in chunks:
        page_id  = chunk["page_id"]
        content  = chunk["content"]
        anchor   = chunk["anchor"]
        typ      = chunk["type"]

        # Separatore di pagina
        if page_id is not None and page_id != current_page:
            current_page = page_id
            lines.append(f"\n---\n<!-- pagina {page_id} -->\n")

        # Inietta anchor se presente
        if anchor is not None:
            content = _inject_anchor(content, anchor, typ)

        lines.append(content)
        lines.append("")  # riga vuota tra elementi

    md_text = "\n".join(lines)
    md_path = output_dir / "document.md"
    md_path.write_text(md_text, encoding="utf-8")
    return md_path


# ─── Bounding box PDF ────────────────────────────────────────────────────────

def _get_label_color(label_str: str) -> tuple[int, int, int]:
    key = label_str.lower().replace(" ", "_").replace("-", "_")
    return LABEL_COLORS.get(key, DEFAULT_COLOR)


def draw_bboxes_on_page(doc_result, page_no: int):
    from PIL import Image, ImageDraw, ImageFont
    doc  = doc_result.document
    page = doc.pages.get(page_no)
    if page is None or page.image is None or page.image.pil_image is None:
        return None
    img: Image.Image = page.image.pil_image.copy().convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    page_h  = page.size.height
    page_w  = page.size.width
    img_w, img_h = img.size
    scale_x = img_w / page_w
    scale_y = img_h / page_h
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    except Exception:
        font = ImageFont.load_default()
    for item, _ in doc.iterate_items():
        if not hasattr(item, "prov") or not item.prov:
            continue
        for prov in item.prov:
            if prov.page_no != page_no:
                continue
            bbox = prov.bbox.to_top_left_origin(page_height=page_h)
            x0, y0 = bbox.l * scale_x, bbox.t * scale_y
            x1, y1 = bbox.r * scale_x, bbox.b * scale_y
            if x1 <= x0 or y1 <= y0:
                continue
            label_str = item.label.value if hasattr(item.label, "value") else str(item.label)
            r, g, b = _get_label_color(label_str)
            draw.rectangle([x0, y0, x1, y1], outline=(r, g, b, 230), width=2,
                           fill=(r, g, b, 30))
            label_short = label_str.replace("_", " ")
            try:
                tb = draw.textbbox((x0 + 2, y0 + 1), label_short, font=font)
                draw.rectangle(tb, fill=(r, g, b, 200))
                draw.text((x0 + 2, y0 + 1), label_short, fill=(255, 255, 255), font=font)
            except Exception:
                draw.text((x0 + 2, y0 + 1), label_short, fill=(r, g, b))
    return img




def build_bbox_pdf(doc_result, output_dir: Path, page_filter: set[int] | None) -> Path | None:
    try:
        from fpdf import FPDF
    except ImportError:
        print("   ⚠️  fpdf2 non trovato (pip install fpdf2). PDF bbox saltato.")
        return None
    doc   = doc_result.document
    pages = sorted(doc.pages.keys())
    pages_to_annotate = [p for p in pages if (page_filter is None or p in page_filter)]
    if not pages_to_annotate:
        return None
    bbox_dir = output_dir / "_bbox_tmp"
    bbox_dir.mkdir(exist_ok=True)
    pdf = FPDF(unit="pt")
    annotated_count = 0
    for page_no in pages_to_annotate:
        annotated = draw_bboxes_on_page(doc_result, page_no)
        if annotated is None:
            print(f"   ⚠️  Pagina {page_no}: immagine non disponibile, saltata.")
            continue
        tmp_path = bbox_dir / f"bbox_page_{page_no:04d}.png"
        annotated.save(str(tmp_path), format="PNG")
        page  = doc.pages[page_no]
        w_pt  = page.size.width
        h_pt  = page.size.height
        pdf.add_page(format=(w_pt, h_pt))
        pdf.image(str(tmp_path), x=0, y=0, w=w_pt, h=h_pt)
        annotated_count += 1
        print(f"   📄 Annotata pagina {page_no}")
    if annotated_count == 0:
        return None
    out_path = output_dir / "annotated_bboxes.pdf"
    pdf.output(str(out_path))
    for f in bbox_dir.glob("*.png"):
        f.unlink()
    bbox_dir.rmdir()
    return out_path




# ── Salvataggio immagini pagina ────────────────────────────────────────────────

def save_page_images(doc_result, output_dir: Path,
                     page_filter: set[int] | None) -> Path:
    """Salva le immagini di ogni pagina come PNG in pages/."""
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    doc = doc_result.document
    saved = 0
    for page_no in sorted(doc.pages.keys()):
        if page_filter and page_no not in page_filter:
            continue
        page = doc.pages[page_no]
        if page.image is None or page.image.pil_image is None:
            continue
        fname = f"page_{page_no:04d}.png"
        page.image.pil_image.save(str(pages_dir / fname), format="PNG")
        saved += 1
    print(f"   ✅ {saved} pagine salvate in pages/")
    return pages_dir


# ── Generazione viewer.html ───────────────────────────────────────────────────

def generate_viewer_html(output_dir: Path, citations: dict) -> Path:
    """Genera viewer.html autoconsistente con tutti i dati delle citazioni.

    Quando aperto con #¶N nel fragment URL, mostra la pagina corrispondente
    con la bbox gialla sovrapposta tramite canvas.
    """
    # Estrai solo le citations (senza metadati wrapper)
    cit_data = citations.get("citations", citations)

    viewer_path = output_dir / "viewer.html"
    viewer_path.write_text(f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Viewer Citazioni</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        background: #1a1a1a; color: #e0e0e0;
        display: flex; flex-direction: column; align-items: center;
        min-height: 100vh; padding: 20px;
    }}
    #toolbar {{
        display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
        margin-bottom: 16px; justify-content: center;
    }}
    #toolbar input {{
        padding: 8px 12px; border: 1px solid #444; border-radius: 6px;
        background: #2a2a2a; color: #fff; font-size: 14px; width: 140px;
    }}
    #toolbar button {{
        padding: 8px 16px; border: none; border-radius: 6px;
        background: #2563eb; color: #fff; font-size: 14px; cursor: pointer;
        font-weight: 600; transition: background 0.15s;
    }}
    #toolbar button:hover {{ background: #1d4ed8; }}
    #nav-buttons {{ display: flex; gap: 6px; }}
    #nav-buttons button {{
        background: #374151; min-width: 36px;
    }}
    #nav-buttons button:hover {{ background: #4b5563; }}
    #viewer {{
        position: relative; display: inline-block;
        background: #fff; box-shadow: 0 4px 24px rgba(0,0,0,0.5);
        border-radius: 4px; overflow: hidden; max-width: 100%;
    }}
    #page-image {{ display: block; max-width: 100%; height: auto; }}
    #bbox-canvas {{
        position: absolute; top: 0; left: 0;
        pointer-events: none;
    }}
    #info-panel {{
        margin-top: 16px; padding: 16px 20px; background: #2a2a2a;
        border-radius: 8px; max-width: 700px; width: 100%;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    }}
    #info-panel .anchor {{ color: #fbbf24; font-weight: 700; font-size: 18px; }}
    #info-panel .meta {{ color: #9ca3af; font-size: 13px; margin: 4px 0 10px; }}
    #info-panel .content {{
        line-height: 1.7; font-size: 14px; color: #d1d5db;
        white-space: pre-wrap;
    }}
    .empty-state {{
        text-align: center; color: #9ca3af; margin-top: 80px;
    }}
    .empty-state h2 {{ font-size: 24px; margin-bottom: 8px; color: #6b7280; }}
</style>
</head>
<body>
<div id="toolbar">
    <span style="color:#9ca3af;font-size:14px;">Anchor:</span>
    <input type="text" id="anchor-input" placeholder="es. ¶42" />
    <button onclick="goToAnchor()">Vai</button>
    <div id="nav-buttons">
        <button onclick="prevAnchor()" title="Precedente">◀</button>
        <button onclick="nextAnchor()" title="Successivo">▶</button>
    </div>
</div>
<div id="viewer">
    <img id="page-image" src="" alt="Pagina" style="display:none;" />
    <canvas id="bbox-canvas"></canvas>
</div>
<div id="info-panel">
    <div id="info-content" class="empty-state">
        <h2>Nessuna citazione selezionata</h2>
        <p>Usa l'input sopra per cercare un anchor (es. ¶42) o i pulsanti ◀ ▶ per navigare.</p>
    </div>
</div>
<script>
const CITATIONS = {json.dumps(cit_data, ensure_ascii=False)};
const ANCHORS = Object.keys(CITATIONS).sort((a, b) => {{
    return parseInt(a.replace('¶', '')) - parseInt(b.replace('¶', ''));
}});

let currentAnchor = null;

function getAnchorFromHash() {{
    const hash = window.location.hash.substring(1);
    if (!hash) return null;
    // Supporta sia "42" (formato link) che "¶42" (formato manuale)
    const anchor = hash.startsWith('¶') ? hash : '¶' + hash;
    if (CITATIONS[anchor]) return anchor;
    return null;
}}

function showAnchor(anchor) {{
    if (!anchor || !CITATIONS[anchor]) {{
        document.getElementById('info-content').innerHTML =
            '<div class="empty-state"><h2>Citazione non trovata</h2><p>Anchor: ' + (anchor || '') + '</p></div>';
        document.getElementById('page-image').style.display = 'none';
        document.getElementById('bbox-canvas').style.display = 'none';
        return;
    }}
    currentAnchor = anchor;
    document.getElementById('anchor-input').value = anchor;
    window.location.hash = anchor.replace('¶', '');

    const cit = CITATIONS[anchor];
    const pageNo = cit.page_id;
    const img = document.getElementById('page-image');
    const canvas = document.getElementById('bbox-canvas');

    img.src = 'pages/page_' + String(pageNo).padStart(4, '0') + '.png';
    img.style.display = 'block';
    img.onload = function() {{
        const scaleX = img.naturalWidth / cit.page_width;
        const scaleY = img.naturalHeight / cit.page_height;

        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        canvas.style.display = 'block';
        canvas.style.width = img.clientWidth + 'px';
        canvas.style.height = img.clientHeight + 'px';

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (cit.bbox) {{
            // bbox in coordinate bottom-left (Docling) → top-left (canvas)
            const x0 = cit.bbox.l * scaleX;
            const y0 = (cit.page_height - cit.bbox.t) * scaleY;
            const x1 = cit.bbox.r * scaleX;
            const y1 = (cit.page_height - cit.bbox.b) * scaleY;
            const w = x1 - x0;
            const h = y1 - y0;

            if (w > 0 && h > 0) {{
                // Fill giallo semi-trasparente
                ctx.fillStyle = 'rgba(255, 230, 50, 0.25)';
                ctx.fillRect(x0, y0, w, h);
                // Outline giallo spesso
                ctx.strokeStyle = 'rgba(255, 200, 0, 1)';
                ctx.lineWidth = 3;
                ctx.strokeRect(x0, y0, w, h);
            }}
        }}
    }};

    document.getElementById('info-content').innerHTML =
        '<div class="anchor">' + anchor + '</div>' +
        '<div class="meta">Pagina ' + cit.page_id + ' · ' + cit.type.replace(/_/g, ' ') + '</div>' +
        '<div class="content">' + escapeHtml(cit.content) + '</div>';
}}

function escapeHtml(text) {{
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}}

function goToAnchor() {{
    const val = document.getElementById('anchor-input').value.trim();
    const anchor = val.startsWith('¶') ? val : '¶' + val;
    if (CITATIONS[anchor]) showAnchor(anchor);
    else alert('Anchor non trovato: ' + anchor);
}}

function nextAnchor() {{
    if (!currentAnchor) {{ showAnchor(ANCHORS[0]); return; }}
    const idx = ANCHORS.indexOf(currentAnchor);
    if (idx >= 0 && idx < ANCHORS.length - 1) showAnchor(ANCHORS[idx + 1]);
}}

function prevAnchor() {{
    if (!currentAnchor) {{ showAnchor(ANCHORS[0]); return; }}
    const idx = ANCHORS.indexOf(currentAnchor);
    if (idx > 0) showAnchor(ANCHORS[idx - 1]);
}}

// Inizializzazione dal fragment URL
const hashAnchor = getAnchorFromHash();
if (hashAnchor) showAnchor(hashAnchor);
else {{
    document.getElementById('page-image').style.display = 'none';
    document.getElementById('bbox-canvas').style.display = 'none';
}}

// Ascolta cambiamenti del fragment (per navigazione da report)
window.addEventListener('hashchange', function() {{
    const anchor = getAnchorFromHash();
    if (anchor) showAnchor(anchor);
}});

// Enter key sull'input
document.getElementById('anchor-input').addEventListener('keydown', function(e) {{
    if (e.key === 'Enter') goToAnchor();
}});
</script>
</body>
</html>
""", encoding="utf-8")
    return viewer_path


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    check_dependencies()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        print(f"❌ File non trovato: {pdf_path}")
        sys.exit(1)
    if pdf_path.suffix.lower() != ".pdf":
        print(f"❌ Il file non è un PDF: {pdf_path}")
        sys.exit(1)

    try:
        page_filter = parse_pages(args.pages)
    except Exception:
        print(f"❌ Formato pagine non valido: '{args.pages}'. Usa es. '1-5' o '1,3,7'.")
        sys.exit(1)

    output_dir = Path(args.output_dir) / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"

    extract_images = not args.no_images
    extract_math   = not args.no_math
    generate_bbox  = not args.no_bbox_pdf
    force_ocr      = args.ocr
    need_page_imgs = True  # sempre: servono per pages/ e viewer.html

    print(f"📁 Output in        : {output_dir}")
    print(f"📑 Pagine           : {', '.join(str(p) for p in sorted(page_filter)) if page_filter else 'tutte'}")
    print(f"🖼  Immagini         : {'✅' if extract_images else '❌'}")
    print(f"➕ Formule (LaTeX)   : {'✅' if extract_math else '❌'}")
    print(f"🔲 PDF bounding box  : {'✅' if generate_bbox else '❌'}")
    print(f"📋 JSON citabile     : ✅")
    print(f"🔍 OCR forzato       : {'✅' if force_ocr else '❌'}")
    print()

    # ── Conversione ───────────────────────────────────────────────────────────
    print("⚙️  Avvio conversione Docling...")
    try:
        doc_result = run_conversion(pdf_path, extract_images, extract_math,
                                    force_ocr, need_page_imgs)
    except Exception as e:
        print(f"❌ Errore conversione: {e}")
        raise

    if page_filter:
        doc = doc_result.document
        all_pages = set(doc.pages.keys())
        for pg in all_pages - page_filter:
            if pg in doc.pages and doc.pages[pg].image:
                doc.pages[pg].image = None

    # ── Immagini ──────────────────────────────────────────────────────────────
    image_map: dict[str, str] = {}
    if extract_images:
        print("\n🔍 Estrazione immagini di figura...")
        image_map = save_images(doc_result, images_dir)
        print(f"   Totale: {len(image_map)}")

    # ── Costruzione chunk (unica passata, condivisa da MD e JSON) ─────────────
    print("\n🧩 Costruzione chunk con anchor...")
    total_pages = len(doc_result.document.pages)
    chunks = build_chunks(doc_result, pdf_path, page_filter, image_map)
    citable = sum(1 for c in chunks if c["anchor"] is not None)
    print(f"   Totale chunk: {len(chunks)}  |  Citabili (con anchor): {citable}")

    # ── Markdown con anchor inline ────────────────────────────────────────────
    print("\n📝 Esportazione Markdown con anchor [¶N]...")
    md_path = export_markdown_with_anchors(chunks, output_dir, page_filter)
    print(f"   ✅ {md_path}")

    # ── JSON indice citazioni (lookup O(1)) ───────────────────────────────────
    print("\n🗂  Generazione indice citazioni (citations.json)...")
    citations = build_citations_index(chunks, pdf_path)
    cit_path = output_dir / "citations.json"
    cit_path.write_text(json.dumps(citations, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   ✅ {cit_path}  ({citations['total_citable']} entry)")

    # ── Salva immagini pagina per viewer ──────────────────────────────────────
    print("\n🖼  Salvataggio immagini pagina...")
    save_page_images(doc_result, output_dir, page_filter)

    # ── Viewer HTML dinamico ──────────────────────────────────────────────────
    print("\n🌐 Generazione viewer HTML dinamico...")
    viewer_path = generate_viewer_html(output_dir, citations)
    print(f"   ✅ {viewer_path}")

    # ── PDF bounding box ──────────────────────────────────────────────────────
    bbox_pdf_path: Path | None = None
    if generate_bbox:
        print("\n🔲 Generazione PDF con bounding box annotate...")
        bbox_pdf_path = build_bbox_pdf(doc_result, output_dir, page_filter)
        if bbox_pdf_path:
            print(f"   ✅ {bbox_pdf_path}")

    # ── Riepilogo ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ Conversione completata!")
    print(f"   📄 Markdown (con anchor)  : {md_path}")
    print(f"   🗂  Indice citazioni       : {cit_path}  ({citations['total_citable']} entry)")
    print(f"   🌐 Viewer HTML dinamico   : {viewer_path}")
    if image_map:
        print(f"   🖼  Immagini              : {images_dir} ({len(image_map)} file)")
    if bbox_pdf_path:
        print(f"   🔲 PDF bbox annotato      : {bbox_pdf_path}")
    print("=" * 60)
    print()
    print("💡 Citazione agente:")
    print('   Markdown:  "…testo… [¶42]"')
    print('   Lookup:    citations["¶42"]  →  {page_id, type, content, paragraph_id}')
    print('   Viewer:    viewer.html#¶42  →  pagina con bbox gialla')


if __name__ == "__main__":
    main()
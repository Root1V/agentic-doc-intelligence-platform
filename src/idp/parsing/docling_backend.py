"""Docling adapter for ``ParserBackend`` — the other candidate compared
against PaddleOCR by ``scripts/compare_ocr_backends.py`` before a default is
fixed with data rather than a priori preference.
"""

from __future__ import annotations

import io

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DocItem, PictureItem, TableItem, TextItem
from docling_core.types.doc.base import Size
from docling_core.types.io import DocumentStream

from idp.config import Settings
from idp.parsing.normalize import ParsedBlock, ParsedDocument, load_pages, page_to_b64

_TABLE_LABEL = "table"
_PICTURE_LABEL = "figure"
_TITLE_LABELS = {"title", "section_header"}


class DoclingBackend:
    name = "docling"

    def __init__(self, settings: Settings) -> None:
        self._converter: DocumentConverter | None = None

    def _engine(self) -> DocumentConverter:
        if self._converter is None:
            self._converter = DocumentConverter()
        return self._converter

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        result = self._engine().convert(DocumentStream(name=filename, stream=io.BytesIO(file_bytes)))
        doc = result.document

        page_sizes: dict[int, Size] = {no: page.size for no, page in doc.pages.items()}
        blocks: list[ParsedBlock] = []
        region_id = 0

        for item, _level in doc.iterate_items():
            if not isinstance(item, DocItem) or not item.prov:
                continue
            prov = item.prov[0]
            page_no = prov.page_no
            size = page_sizes.get(page_no)
            if size is None:
                continue
            norm_bbox = prov.bbox.to_top_left_origin(size.height).normalized(size)
            bbox = [norm_bbox.l, norm_bbox.t, norm_bbox.r, norm_bbox.b]

            if isinstance(item, TableItem):
                text = item.export_to_markdown(doc)
                block_type = _TABLE_LABEL
            elif isinstance(item, PictureItem):
                text = item.caption_text(doc)
                block_type = _PICTURE_LABEL
            elif isinstance(item, TextItem):
                text = item.text
                block_type = "title" if str(item.label) in _TITLE_LABELS else "text"
            else:
                continue

            blocks.append(
                ParsedBlock(
                    region_id=region_id,
                    text=text,
                    page=page_no - 1,  # docling pages are 1-indexed; keep 0-indexed internally
                    bbox=bbox,
                    confidence=1.0,  # docling does not expose a per-element confidence score
                    block_type=block_type,
                )
            )
            region_id += 1

        pages = load_pages(file_bytes, filename)
        page_images_b64 = {i: page_to_b64(p) for i, p in enumerate(pages)}

        return ParsedDocument(backend=self.name, page_count=len(doc.pages) or len(pages), blocks=blocks, page_images_b64=page_images_b64)

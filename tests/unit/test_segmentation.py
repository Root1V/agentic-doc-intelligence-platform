"""Segmentation exists to handle a real case found in practice: a single
physical PDF upload that actually bundles several distinct logical documents
(2026-08-23: '302_Cronograma subrogado-Estado de cuenta' — an email cover,
a payment schedule, contract T&Cs, and an account statement, all in one
7-page file), which timed out when forced through one classify->extract
pass. These tests cover the parts that don't require a live LLM call: the
page-range slicing helper, and the single-page fast path that skips the LLM
call entirely."""

from __future__ import annotations

from idp.parsing.normalize import ParsedBlock, ParsedDocument, slice_by_pages
from idp.segmentation.splitter import DocumentSegment, detect_segments


def _parsed_three_pages() -> ParsedDocument:
    return ParsedDocument(
        backend="test",
        page_count=3,
        blocks=[
            ParsedBlock(region_id=0, text="page0 block", page=0, bbox=[0, 0, 1, 1], confidence=0.9),
            ParsedBlock(region_id=1, text="page1 block a", page=1, bbox=[0, 0, 1, 1], confidence=0.9),
            ParsedBlock(region_id=2, text="page1 block b", page=1, bbox=[0, 0, 1, 1], confidence=0.9),
            ParsedBlock(region_id=3, text="page2 block", page=2, bbox=[0, 0, 1, 1], confidence=0.9),
        ],
        page_images_b64={0: "img0", 1: "img1", 2: "img2"},
    )


def test_slice_by_pages_keeps_absolute_page_numbers():
    parsed = _parsed_three_pages()
    sliced = slice_by_pages(parsed, 1, 2)
    assert {b.region_id for b in sliced.blocks} == {1, 2, 3}
    assert all(b.page in (1, 2) for b in sliced.blocks)
    assert set(sliced.page_images_b64) == {1, 2}
    # page_count stays the ORIGINAL document's count, not the slice's — the
    # slice is a view into one physical upload, not a document of its own.
    assert sliced.page_count == 3


def test_slice_by_pages_single_page():
    parsed = _parsed_three_pages()
    sliced = slice_by_pages(parsed, 0, 0)
    assert {b.region_id for b in sliced.blocks} == {0}
    assert set(sliced.page_images_b64) == {0}


def test_detect_segments_single_page_skips_llm_call():
    parsed = ParsedDocument(
        backend="test",
        page_count=1,
        blocks=[ParsedBlock(region_id=0, text="only page", page=0, bbox=[0, 0, 1, 1], confidence=0.9)],
    )
    # settings=None would blow up if this path ever tried to make an LLM
    # call — the fast path must never touch settings for a single-page doc.
    segments = detect_segments(None, parsed)  # type: ignore[arg-type]
    assert segments == [DocumentSegment(start_page=0, end_page=0, reasoning=segments[0].reasoning)]

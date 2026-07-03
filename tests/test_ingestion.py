from pathlib import Path

from graph.configs import PAPERS_DIR, PROCESSED_DIR
from graph.ingestion.loader import PDFLoader
from graph.ingestion.cleaner import TextCleaner
from graph.ingestion.exporter import DocumentExporter


# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------

def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def preview(text: str, limit: int = 700):
    if not text:
        print("<EMPTY>")
        return

    print(text[:limit])

    if len(text) > limit:
        print("\n...[TRUNCATED]...")


# ---------------------------------------------------------
# STEP 1 : Loader
# ---------------------------------------------------------

def test_loader(pdf_path: Path):

    divider("STEP 1 : PDF LOADER")

    loader = PDFLoader()

    document = loader.load(pdf_path)

    print(document)

    print("\nPaper ID :", document.paper_id)
    print("Filename :", document.filename)
    print("Path     :", document.file_path)

    divider("METADATA")

    for key, value in document.metadata.items():
        print(f"{key:<15}: {value}")

    divider("RAW TEXT PREVIEW")

    preview(document.raw_text)

    return document


# ---------------------------------------------------------
# STEP 2 : Cleaner
# ---------------------------------------------------------

def test_cleaner(document):

    divider("STEP 2 : TEXT CLEANER")

    cleaner = TextCleaner()

    cleaned_document = cleaner.clean(document)

    divider("CLEANED TEXT PREVIEW")

    preview(cleaned_document.cleaned_text)

    return cleaned_document


# ---------------------------------------------------------
# STEP 3 : Exporter
# ---------------------------------------------------------

def test_exporter(document):

    divider("STEP 3 : EXPORTER")

    exporter = DocumentExporter(PROCESSED_DIR)

    json_path = exporter.save(document)

    print("Saved JSON:")
    print(json_path)

    divider("STEP 4 : LOAD JSON")

    loaded_document = exporter.load(json_path)

    print(loaded_document)

    return loaded_document


# ---------------------------------------------------------
# Sanity Checks
# ---------------------------------------------------------

def sanity_checks(original, loaded):

    divider("SANITY CHECKS")

    assert original.paper_id == loaded.paper_id
    print("✓ paper_id preserved")

    assert original.filename == loaded.filename
    print("✓ filename preserved")

    assert original.file_path == loaded.file_path
    print("✓ file path preserved")

    assert original.raw_text == loaded.raw_text
    print("✓ raw text preserved")

    assert original.cleaned_text == loaded.cleaned_text
    print("✓ cleaned text preserved")

    assert original.metadata == loaded.metadata
    print("✓ metadata preserved")

    assert len(original.raw_text) > 0
    print("✓ raw text extracted")

    assert len(original.cleaned_text) > 0
    print("✓ cleaned text generated")

    print("\n ALL SANITY CHECKS PASSED")


# ---------------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------------

def run_pipeline(pdf_path: Path):

    divider("GRAPHRAG INGESTION PIPELINE TEST")

    document = test_loader(pdf_path)

    document = test_cleaner(document)

    loaded_document = test_exporter(document)

    sanity_checks(document, loaded_document)

    divider("PIPELINE SUMMARY")

    raw_len = len(document.raw_text)
    clean_len = len(document.cleaned_text)

    print(f"Raw Characters      : {raw_len}")
    print(f"Clean Characters    : {clean_len}")
    print(f"Characters Removed  : {raw_len-clean_len}")

    if raw_len > 0:
        reduction = ((raw_len - clean_len) / raw_len) * 100
        print(f"Reduction           : {reduction:.2f}%")

    divider("TEST COMPLETE")

    print("-> Loader Passed")
    print("-> Cleaner Passed")
    print("-> Exporter Passed")
    print("-> JSON Reload Passed")
    print("-> Entire Ingestion Pipeline Passed")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    pdf_file = PAPERS_DIR / "1-Attention Is All You Need.pdf"

    print("Testing PDF:")
    print(pdf_file.resolve())

    if not pdf_file.exists():
        print("\n❌ PDF not found")
    else:
        run_pipeline(pdf_file)
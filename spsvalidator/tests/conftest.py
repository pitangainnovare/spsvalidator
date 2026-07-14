from pathlib import Path

import pytest
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po


@pytest.fixture(scope="session", autouse=True)
def compile_gettext_catalogs():
    translations_dir = (
        Path(__file__).resolve().parents[1] / "src" / "spsvalidator" / "translations"
    )
    for po_path in translations_dir.glob("*/LC_MESSAGES/messages.po"):
        with po_path.open(encoding="utf-8") as po_file:
            catalog = read_po(po_file)
        with po_path.with_suffix(".mo").open("wb") as mo_file:
            write_mo(mo_file, catalog)

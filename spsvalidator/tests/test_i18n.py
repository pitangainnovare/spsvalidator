from pathlib import Path

from babel.messages.pofile import read_po

from spsvalidator.web import i18n


def test_normalize_language_handles_system_locale():
    assert i18n.normalize_language("pt_BR") == "pt"
    assert i18n.normalize_language("en-US") == "en"
    assert i18n.normalize_language("es_AR") == "es"
    assert i18n.normalize_language("de_DE") is None
    assert i18n.normalize_language(None) is None


def test_gettext_catalogs_exist_for_all_supported_languages():
    translations_dir = (
        Path(__file__).resolve().parents[1] / "src" / "spsvalidator" / "translations"
    )
    for language in i18n.SUPPORTED_LANGUAGES:
        catalog_dir = translations_dir / language / "LC_MESSAGES"
        assert (catalog_dir / "messages.po").is_file()

    with (translations_dir / "en" / "LC_MESSAGES" / "messages.po").open(
        encoding="utf-8"
    ) as catalog:
        translations = read_po(catalog)
    assert translations.get("Validação de pacotes SPS").string == (
        "SPS package validation"
    )

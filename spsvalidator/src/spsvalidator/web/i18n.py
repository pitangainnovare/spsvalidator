from __future__ import annotations

SUPPORTED_LANGUAGES = ("pt", "en", "es")

LANGUAGE_OPTIONS = (
    {"code": "pt", "flag": "🇧🇷", "label": "Português"},
    {"code": "en", "flag": "🇺🇸", "label": "English"},
    {"code": "es", "flag": "🇪🇸", "label": "Español"},
)

TRANSLATIONS = {
    "pt": {
        "html_lang": "pt-BR",
        "subtitle": "Validação de pacotes SPS",
        "validate_package": "Validar pacote SPS",
        "validate": "Validar",
        "select_zip": "Selecione um arquivo .zip para validar.",
        "zip_only": "Apenas arquivos .zip SPS sao suportados.",
        "validated_packages": "Pacotes validados",
        "no_packages_yet": "Nenhum pacote validado ainda.",
        "date": "Data",
        "package": "Pacote",
        "status": "Status",
        "xmls": "XMLs",
        "issues": "Questões",
        "exceptions": "Exceptions",
        "critical": "CRITICAL",
        "error": "ERROR",
        "warning": "WARNING",
        "download_csv": "Relatório",
        "csv_saved": "Arquivo salvo em {path}",
        "csv_download_failed": "Falha ao baixar CSV.",
        "validation_result": "Artigos Considerados",
        "articles_found": "Artigos encontrados",
        "xml_file": "Arquivo XML",
        "title": "Título",
        "authors": "Autores",
        "validation_issues": "Questões a resolver",
        "no_exceptions": "Sem exceptions.",
        "detail": "Detalhe",
        "footer_built_for_macos": "Compilado para macOS {version}",
        "footer_dev_build": "Build de desenvolvimento ({platform})",
        "status_valid": "valid",
        "status_invalid": "invalid",
        "status_error": "error",
        "status_ok": "ok",
        "status_issue": "issue",
    },
    "en": {
        "html_lang": "en",
        "subtitle": "SPS package validation",
        "validate_package": "Validate SPS package",
        "validate": "Validate",
        "select_zip": "Select a .zip file to validate.",
        "zip_only": "Only SPS .zip files are supported.",
        "validated_packages": "Validated packages",
        "no_packages_yet": "No packages validated yet.",
        "date": "Date",
        "package": "Package",
        "status": "Status",
        "xmls": "XMLs",
        "issues": "Questions",
        "exceptions": "Exceptions",
        "critical": "CRITICAL",
        "error": "ERROR",
        "warning": "WARNING",
        "download_csv": "Report",
        "csv_saved": "File saved to {path}",
        "csv_download_failed": "Failed to download CSV.",
        "validation_result": "Articles Considered",
        "articles_found": "Articles found",
        "xml_file": "XML file",
        "title": "Title",
        "authors": "Authors",
        "validation_issues": "Questions to resolve",
        "no_exceptions": "No exceptions.",
        "detail": "Detail",
        "footer_built_for_macos": "Built for macOS {version}",
        "footer_dev_build": "Development build ({platform})",
        "status_valid": "valid",
        "status_invalid": "invalid",
        "status_error": "error",
        "status_ok": "ok",
        "status_issue": "issue",
    },
    "es": {
        "html_lang": "es",
        "subtitle": "Validación de paquetes SPS",
        "validate_package": "Validar paquete SPS",
        "validate": "Validar",
        "select_zip": "Seleccione un archivo .zip para validar.",
        "zip_only": "Solo se admiten archivos .zip SPS.",
        "validated_packages": "Paquetes validados",
        "no_packages_yet": "Ningún paquete validado todavía.",
        "date": "Fecha",
        "package": "Paquete",
        "status": "Estado",
        "xmls": "XMLs",
        "issues": "Cuestiones",
        "exceptions": "Exceptions",
        "critical": "CRITICAL",
        "error": "ERROR",
        "warning": "WARNING",
        "download_csv": "Informe",
        "csv_saved": "Archivo guardado en {path}",
        "csv_download_failed": "Error al descargar CSV.",
        "validation_result": "Artículos Considerados",
        "articles_found": "Artículos encontrados",
        "xml_file": "Archivo XML",
        "title": "Título",
        "authors": "Autores",
        "validation_issues": "Cuestiones a resolver",
        "no_exceptions": "Sin exceptions.",
        "detail": "Detalle",
        "footer_built_for_macos": "Compilado para macOS {version}",
        "footer_dev_build": "Build de desarrollo ({platform})",
        "status_valid": "valid",
        "status_invalid": "invalid",
        "status_error": "error",
        "status_ok": "ok",
        "status_issue": "issue",
    },
}


def normalize_language(code, default="pt"):
    if not code:
        return default

    normalized = code.lower().replace("_", "-").split("-", 1)[0]
    if normalized in SUPPORTED_LANGUAGES:
        return normalized

    return default


def detect_request_language(
    request,
    execution_mode="browser",
    system_language=None,
    preferred_language=None,
):
    persisted_language = normalize_language(preferred_language, None)
    if persisted_language:
        return persisted_language

    if execution_mode == "browser":
        browser_language = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
        return normalize_language(browser_language)

    return normalize_language(system_language)


def get_translations(language: str) -> dict[str, str]:
    return TRANSLATIONS[normalize_language(language)]

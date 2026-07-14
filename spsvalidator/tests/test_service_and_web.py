import io
import zipfile
from pathlib import Path

import pytest

from spsvalidator.app import create_app
from spsvalidator.services import validation_service


def _zip_fixture_xml() -> io.BytesIO:
    fixture_path = (
        Path(__file__).resolve().parents[3] / "fixtures" / "xml" / "dias_2023.xml"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("dias_2023.xml", fixture_path.read_bytes())
    buffer.seek(0)
    return buffer


def test_run_validation_persists_result(monkeypatch, tmp_path):
    app = create_app(str(tmp_path))
    db_path = app.config["DB_PATH"]

    def fake_validate(zip_path: str):
        return {
            "rows": [{"group": "g", "title": "t", "response": "ERROR"}],
            "exceptions": [],
            "articles": [
                {
                    "xml_path": "dias_2023.xml",
                    "title": "Article",
                    "authors_text": "A B",
                    "doi": "10.1/2",
                    "pid": "abc",
                    "article_status": "issue",
                    "issue_count": 1,
                }
            ],
        }

    monkeypatch.setattr(validation_service, "validate_sps_zip", fake_validate)
    payload = _zip_fixture_xml()

    class UploadedFile:
        filename = "package.zip"

        def save(self, destination):
            Path(destination).write_bytes(payload.getvalue())

    result = validation_service.run_validation(db_path, UploadedFile())
    assert result["status"] == "invalid"
    assert result["issues_count"] == 1
    assert result["xml_count"] == 1

    client = app.test_client()
    csv_response = client.get(f"/validation/{result['history_id']}/report.csv")
    assert csv_response.status_code == 200
    assert csv_response.headers["Content-Type"] == "application/octet-stream"
    assert "attachment" in csv_response.headers["Content-Disposition"]
    assert b"group,title" in csv_response.data
    assert b"ERROR" in csv_response.data


def test_run_validation_persists_bytes_in_report(monkeypatch, tmp_path):
    app = create_app(str(tmp_path))
    db_path = app.config["DB_PATH"]

    def fake_validate(zip_path: str):
        return {
            "rows": [
                {
                    "group": "g",
                    "title": "t",
                    "response": "ERROR",
                    "expected_value": b"expected",
                    "got_value": b"got",
                }
            ],
            "exceptions": [{"response": "exception", "detail": b"fail"}],
            "articles": [
                {
                    "xml_path": "article.xml",
                    "title": "Article",
                    "authors_text": "A B",
                    "doi": "",
                    "pid": "",
                    "article_status": "issue",
                    "issue_count": 1,
                }
            ],
        }

    monkeypatch.setattr(validation_service, "validate_sps_zip", fake_validate)

    class UploadedFile:
        filename = "package.zip"

        def save(self, destination):
            Path(destination).write_bytes(b"zip")

    result = validation_service.run_validation(db_path, UploadedFile())
    client = app.test_client()
    response = client.get(f"/validation/{result['history_id']}/report.csv")
    assert response.status_code == 200
    assert b"expected" in response.data
    assert b"got" in response.data


def test_validate_route_shows_error_on_failure(monkeypatch, tmp_path):
    app = create_app(str(tmp_path))

    def fake_validate(zip_path: str):
        raise RuntimeError("validation failed")

    monkeypatch.setattr(validation_service, "validate_sps_zip", fake_validate)
    client = app.test_client()
    response = client.post(
        "/validate",
        data={"package_zip": (_zip_fixture_xml(), "package.zip")},
        content_type="multipart/form-data",
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "validation failed" in html


@pytest.mark.parametrize(
    ("accept_language", "expected"),
    [
        ("pt-BR,pt;q=0.9", "Validação de pacotes SPS"),
        ("en-US,en;q=0.9", "SPS package validation"),
        ("es-AR,es;q=0.9", "Validación de paquetes SPS"),
    ],
)
def test_browser_uses_accept_language(tmp_path, accept_language, expected):
    app = create_app(str(tmp_path), execution_mode="browser")
    client = app.test_client()
    response = client.get("/", headers={"Accept-Language": accept_language})

    assert expected in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("system_language", "expected", "unexpected"),
    [
        ("pt_BR", "Validação de pacotes SPS", "SPS package validation"),
        ("en_US", "SPS package validation", "Validação de pacotes SPS"),
        ("es_AR", "Validación de paquetes SPS", "SPS package validation"),
    ],
)
def test_desktop_uses_system_language(
    tmp_path,
    system_language,
    expected,
    unexpected,
):
    app = create_app(
        str(tmp_path),
        execution_mode="desktop",
        system_language=system_language,
    )
    response = app.test_client().get(
        "/",
        headers={"Accept-Language": "en-US"},
    )
    html = response.get_data(as_text=True)

    assert expected in html
    assert unexpected not in html


@pytest.mark.parametrize(
    ("execution_mode", "system_language", "headers"),
    [
        ("desktop", "de_DE", {"Accept-Language": "en-US"}),
        ("desktop", None, {"Accept-Language": "es-AR"}),
        ("browser", None, {"Accept-Language": "de-DE"}),
        ("browser", None, {}),
    ],
)
def test_unsupported_or_missing_locale_falls_back_to_portuguese(
    tmp_path,
    execution_mode,
    system_language,
    headers,
):
    app = create_app(
        str(tmp_path),
        execution_mode=execution_mode,
        system_language=system_language,
    )
    response = app.test_client().get("/", headers=headers)
    html = response.get_data(as_text=True)

    assert '<html lang="pt">' in html
    assert "Validação de pacotes SPS" in html


def test_python_and_javascript_messages_use_detected_language(tmp_path):
    app = create_app(str(tmp_path), execution_mode="browser")
    response = app.test_client().post(
        "/validate",
        headers={"Accept-Language": "en-US"},
    )
    html = response.get_data(as_text=True)

    assert "Select a .zip file to validate." in html
    assert "File saved to {path}" in html
    assert "Failed to download CSV." in html
    assert "Development build" in html or "Built for macOS" in html


def test_validate_route_processes_upload(monkeypatch, tmp_path):
    app = create_app(str(tmp_path))
    app.testing = True

    def fake_validate(zip_path: str):
        return {
            "rows": [],
            "exceptions": [],
            "articles": [
                {
                    "xml_path": "dias_2023.xml",
                    "title": "T",
                    "authors_text": "Author",
                    "doi": "",
                    "pid": "",
                    "article_status": "ok",
                    "issue_count": 0,
                }
            ],
        }

    monkeypatch.setattr(validation_service, "validate_sps_zip", fake_validate)
    client = app.test_client()
    response = client.post(
        "/validate",
        data={"package_zip": (_zip_fixture_xml(), "package.zip")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Pacotes validados" in html
    assert "package.zip" in html
    assert "img/icon.png" in html
    assert "SPSValidator-v" in html

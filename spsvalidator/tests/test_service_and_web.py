import io
import zipfile
from pathlib import Path

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


def test_set_language_switches_ui_text(tmp_path):
    app = create_app(str(tmp_path))
    client = app.test_client()
    response = client.get("/language/en")
    assert response.status_code == 302

    reopened_app = create_app(str(tmp_path))
    home = reopened_app.test_client().get(
        "/", headers={"Accept-Language": "pt-BR"}
    )
    html = home.get_data(as_text=True)
    assert "SPS package validation" in html
    assert "Built for macOS" in html or "Development build" in html


def test_index_uses_accept_language_when_no_manual_selection(tmp_path):
    app = create_app(str(tmp_path), system_language="pt_BR")
    client = app.test_client()

    responses = (
        client.get("/", headers={"Accept-Language": "en-US,en;q=0.9"}),
        client.get("/", headers={"Accept-Language": "es-ES,es;q=0.9"}),
    )

    assert responses[0].status_code == 200
    assert "SPS package validation" in responses[0].get_data(as_text=True)
    assert responses[1].status_code == 200
    assert "Validación de paquetes SPS" in responses[1].get_data(as_text=True)


def test_index_uses_desktop_system_language_and_ignores_accept_language(tmp_path):
    app = create_app(
        str(tmp_path), execution_mode="desktop", system_language="es_AR"
    )
    client = app.test_client()

    response = client.get("/", headers={"Accept-Language": "en-US,en;q=0.9"})

    assert response.status_code == 200
    assert "Validación de paquetes SPS" in response.get_data(as_text=True)


def test_last_language_selection_is_shared_between_execution_modes(tmp_path):
    browser_app = create_app(str(tmp_path))
    browser_client = browser_app.test_client()
    browser_client.get("/language/en")
    browser_client.get("/language/es")

    desktop_app = create_app(
        str(tmp_path), execution_mode="desktop", system_language="pt_BR"
    )
    response = desktop_app.test_client().get(
        "/", headers={"Accept-Language": "en-US"}
    )

    assert response.status_code == 200
    assert "Validación de paquetes SPS" in response.get_data(as_text=True)


def test_index_falls_back_to_portuguese_for_unsupported_languages(tmp_path):
    app = create_app(
        str(tmp_path), execution_mode="desktop", system_language="de_DE"
    )
    client = app.test_client()

    response = client.get("/", headers={"Accept-Language": "fr-FR"})

    assert response.status_code == 200
    assert "Validação de pacotes SPS" in response.get_data(as_text=True)


def test_validate_uses_the_same_detected_language_as_the_template(tmp_path):
    app = create_app(str(tmp_path))
    client = app.test_client()

    response = client.post("/validate", headers={"Accept-Language": "es-ES"})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Validación de paquetes SPS" in html
    assert "Seleccione un archivo .zip para validar." in html


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
    assert "lang-option" in html

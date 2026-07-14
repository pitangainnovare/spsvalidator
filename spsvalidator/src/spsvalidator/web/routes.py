from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from spsvalidator.db.repository import (
    get_validation_details,
    list_validations,
    set_setting,
)
from spsvalidator.domain.export import build_validation_csv
from spsvalidator.services.validation_service import run_validation
from spsvalidator.web.i18n import get_translations, normalize_language

web_blueprint = Blueprint(
    "web",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)


def _render_index(**context):
    context.setdefault("error_message", None)
    return render_template(
        "index.html",
        history_items=list_validations(current_app.config["DB_PATH"]),
        **context,
    )


def _safe_redirect_target(next_url: str | None) -> str:
    if not next_url:
        return url_for("web.index")
    parsed_url = urlparse(next_url)
    if not parsed_url.netloc and parsed_url.path.startswith("/"):
        return next_url
    return url_for("web.index")


@web_blueprint.get("/")
def index():
    selected_id = request.args.get("history_id")
    details = (
        get_validation_details(current_app.config["DB_PATH"], selected_id)
        if selected_id
        else None
    )
    return _render_index(latest_result=details)


@web_blueprint.post("/validate")
def validate():
    translations = get_translations(g.language)
    uploaded_file = request.files.get("package_zip")
    if uploaded_file is None or not uploaded_file.filename:
        return _render_index(
            latest_result=None,
            error_message=translations["select_zip"],
        )
    try:
        result = run_validation(
            current_app.config["DB_PATH"],
            uploaded_file,
            zip_only_message=translations["zip_only"],
        )
    except Exception as exc:
        return _render_index(latest_result=None, error_message=str(exc))
    return redirect(url_for("web.index", history_id=result["history_id"]))


@web_blueprint.get("/validation/<history_id>/report.csv")
def download_csv(history_id: str):
    details = get_validation_details(current_app.config["DB_PATH"], history_id)
    if details is None:
        abort(404)
    csv_content = build_validation_csv(details["rows"])
    response = make_response(csv_content.encode("utf-8"))
    response.headers["Content-Type"] = "application/octet-stream"
    package_stem = details["package_name"].rsplit(".", 1)[0]
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{package_stem}.validation.csv"'
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@web_blueprint.get("/language/<language_code>")
def set_language(language_code: str):
    language = normalize_language(language_code)
    redirect_target = _safe_redirect_target(request.args.get("next"))
    set_setting(current_app.config["DB_PATH"], "language", language)
    return redirect(redirect_target)


@web_blueprint.get("/favicon.ico")
def favicon():
    static_dir = Path(__file__).resolve().parent / "static" / "img"
    return send_from_directory(static_dir, "icon.png", mimetype="image/png")

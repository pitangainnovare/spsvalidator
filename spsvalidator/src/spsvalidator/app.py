from __future__ import annotations

from pathlib import Path

from flask import Flask, current_app, request
from flask_babel import Babel, get_locale

from spsvalidator.build_metadata import get_footer_build_label
from spsvalidator.db.repository import init_db
from spsvalidator.version import APP_DISPLAY_NAME
from spsvalidator.web import i18n
from spsvalidator.web.routes import web_blueprint


def select_locale():
    if current_app.config["EXECUTION_MODE"] == "desktop":
        return i18n.normalize_language(current_app.config["SYSTEM_LANGUAGE"])

    return request.accept_languages.best_match(i18n.SUPPORTED_LANGUAGES)


def create_app(
    data_dir: str | None = None,
    execution_mode="browser",
    system_language=None,
) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.secret_key = "spsvalidator-local-secret"
    target_dir = Path(data_dir) if data_dir else Path.home() / ".spsvalidator"
    target_dir.mkdir(parents=True, exist_ok=True)
    db_path = target_dir / "spsvalidator.sqlite3"
    init_db(str(db_path))
    app.config["DB_PATH"] = str(db_path)
    app.config["APP_DISPLAY_NAME"] = APP_DISPLAY_NAME
    app.config["BABEL_DEFAULT_LOCALE"] = "pt"
    app.config["EXECUTION_MODE"] = execution_mode
    app.config["SYSTEM_LANGUAGE"] = system_language

    Babel(app, locale_selector=select_locale)

    @app.context_processor
    def inject_app_info():
        return {
            "app_display_name": app.config["APP_DISPLAY_NAME"],
            "current_locale": str(get_locale()).replace("_", "-"),
            "footer_build_label": get_footer_build_label(),
        }

    app.register_blueprint(web_blueprint)
    return app

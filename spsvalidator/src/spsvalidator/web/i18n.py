SUPPORTED_LANGUAGES = ("pt", "en", "es")


def normalize_language(locale_name):
    if not locale_name:
        return None

    language = locale_name.replace("-", "_").split("_", 1)[0].lower()
    return language if language in SUPPORTED_LANGUAGES else None

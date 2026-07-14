from __future__ import annotations

import platform

from flask_babel import gettext

from spsvalidator import build_info


def get_footer_build_label() -> str:
    if (
        build_info.BUILD_MACOS_VERSION != "development"
        and build_info.BUILD_PLATFORM == "macOS"
    ):
        return gettext(
            "Compilado para macOS %(version)s",
            version=build_info.BUILD_MACOS_VERSION,
        )

    runtime_platform = platform.system()

    if runtime_platform == "Darwin":
        mac_version = platform.mac_ver()[0]
        build_number = platform.mac_ver()[2]
        version_label = mac_version

        if build_number:
            version_label = f"{mac_version} ({build_number})"

        return gettext("Compilado para macOS %(version)s", version=version_label)

    return gettext(
        "Build de desenvolvimento (%(platform)s)",
        platform=runtime_platform,
    )

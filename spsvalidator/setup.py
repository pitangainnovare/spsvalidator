from pathlib import Path

from babel.messages.frontend import compile_catalog
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPy(build_py):
    def run(self):
        super().run()

        command = compile_catalog(self.distribution)
        command.directory = str(
            Path(self.build_lib) / "spsvalidator" / "translations"
        )
        command.finalize_options()
        if command.run():
            raise RuntimeError("Could not compile gettext catalogs")


setup(cmdclass={"build_py": BuildPy})

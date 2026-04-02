from setuptools import setup


setup(
    name="codex-history-manager",
    version="0.1.0",
    description="Manage local Codex history: search, export, migrate, clone, rebind provider, and perform guarded history rewrites.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Zhong",
    license="MIT",
    python_requires=">=3.9",
    py_modules=["codex_history_manager"],
    packages=["scripts"],
    entry_points={
        "console_scripts": [
            "codex-history-manager=codex_history_manager:main",
        ]
    },
)

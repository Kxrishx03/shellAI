from setuptools import setup

setup(
    name        = "shellai",
    version     = "0.1.0",
    description = "Run developer tasks by describing them in plain English",
    python_requires = ">=3.8",
    install_requires = [
        "requests",
        "colorama",
        "scikit-learn",
    ],

    entry_points = {
        "console_scripts": [
            "shellai=main:main",
        ],
    },
    py_modules = [
        "main", "ai", "ollama_engine", "local_engine",
        "placeholders", "profiles", "confirm",
        "executor", "config", "dataset_builder",
        # ── previously missing ──────────────────
        "db",
        "display",
        "safety",
        "intent",
    ],
    package_data = {"": ["data/*.json", "data/*.sql"]},
    include_package_data = True,
)
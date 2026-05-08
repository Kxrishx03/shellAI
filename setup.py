from setuptools import setup, find_packages

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
        "executor", "config", "dataset_builder"
    ],
    package_data = {"": ["data/*.json"]},
    include_package_data = True,
)
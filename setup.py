from setuptools import setup, find_packages

setup(
    name="shellai",
    version="0.1.0",
    description="Run tasks by describing them in plain English",
    author="Your Name",
    python_requires=">=3.8",

    install_requires=[
        "requests",
        "colorama",
    ],

    entry_points={
        "console_scripts": [
            "shellai=main:main",
        ],
    },

    
    py_modules=["main", "ai", "executor", "confirm", "config"],
)
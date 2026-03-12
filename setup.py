"""Setup script for RitualFlow."""

from setuptools import setup, find_packages

setup(
    name="ritualflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.40.0",
        "notion-client>=2.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ritualflow=ritualflow.cli:main",
        ],
    },
    python_requires=">=3.11",
)

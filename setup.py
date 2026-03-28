#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="miniclaw-os",
    version="0.1.0",
    author="Syndicate-Alpha",
    author_email="contact@syndicate-alpha.com",
    description="Agent Operating System with industrial safeguards and exponential learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Syndicate-Alpha/miniclaw-os",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "telegram": [
            "python-telegram-bot>=20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "miniclaw=miniclaw_os.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
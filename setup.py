"""Setup script for Telegram Automation Tool."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="telegram-automation",
    version="0.1.0",
    author="Your Name",
    description="Tool tự động hóa các thao tác trên Telegram Web",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.0",
        "pydantic-settings>=2.5.0",
    ],
    entry_points={
        "console_scripts": [
            "telegram-automation-api=api.main:app",
        ],
    },
)


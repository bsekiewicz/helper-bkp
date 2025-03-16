import os

from setuptools import setup, find_packages

with open("VERSION", "r", encoding="utf-8") as f:
    __version__ = f.read().strip()

readme_path = "README.md"
long_description = open(readme_path, "r", encoding="utf-8").read() if os.path.exists(readme_path) else ""

setup(
    name="helper",
    version=__version__,
    url="https://dev.azure.com/webdatawatch/argus/_git/py-pkg-helper",
    author="Bartosz Sękiewicz",
    author_email="bartosz.pawel.sekiewicz@gmail.com",
    description="Utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="utils, postgres, s3",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(include=["helper", "helper.*"]),
    python_requires=">=3.10",
    install_requires=[
        "dateparser==1.2.*",
        "pandas==2.2.*",
        "psycopg2==2.9.*",
        "minio==7.2.*",
        "openpyxl==3.1.*",
        "igraph==0.11.*",
        "price-parser==0.4.*",
        "pyarrow==19.0.*",
        "requests==2.32.*",
    ],
    include_package_data=True,
    package_data={
        "helper": ["data/mappings/*.json"],
    },
)

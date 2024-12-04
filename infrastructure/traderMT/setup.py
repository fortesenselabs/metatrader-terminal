import io

from setuptools import setup, find_packages


def readme():
    with io.open("README.md", encoding="utf-8") as f:
        return f.read()


def requirements(filename):
    reqs = list()
    with io.open(filename, encoding="utf-8") as f:
        for line in f.readlines():
            reqs.append(line.strip())
    return reqs


# Version: 3.17
setup(
    name="traderMT",
    version="3.17",
    packages=find_packages(),
    url="https://github.com/fortesenselabs/metatrader-terminal",
    license="GPL-3.0",
    author="",
    author_email="",
    description="Metatrader EA API",
    long_description=readme(),
    long_description_content_type="text/markdown",
    install_requires=requirements(filename="requirements.txt"),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3",
    keywords=", ".join(
        [
            "metatrader",
            "f-api",
            "historical-data",
            "financial-data",
            "stocks",
            "funds",
            "etfs",
            "indices",
            "currency crosses",
            "bonds",
            "commodities",
            "crypto currencies",
        ]
    ),
    project_urls={
        "Bug Reports": "https://github.com/fortesenselabs/metatrader-terminal/issues",
        "Source": "https://github.com/fortesenselabs/metatrader-terminal",
        # "Documentation": "https://ejtrader.readthedocs.io/",
    },
)

#!/bin/bash

python -m build
rm -rf dist/*
python setup.py sdist bdist_wheel
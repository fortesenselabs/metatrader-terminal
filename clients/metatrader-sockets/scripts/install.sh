#!/bin/bash

python -m pip install --upgrade pip
pip install twine build
pip install --upgrade setuptools wheel
pip install dist/*.whl
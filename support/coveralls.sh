#!/bin/bash

root="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."

cd $root

pip install -r requirements.txt
pip install coveralls
pip install pyyaml

coverage run tests/test.py
coveralls

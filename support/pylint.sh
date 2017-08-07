#!/bin/bash

root="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."

cd $root

pip install pylint
pylint --rcfile .pylintrc crutch

#!/bin/bash
set -e -x

PYTHON_VERSIONS=$1
MANYLINUX_PLATFORM=$2

cd /github/workspace


# RUN python3 setup.py build --debug
#RUN /opt/python/cp37-cp37m/bin/python setup.py build --debug
# TODO path from manylinux. Matrix with python versions

# for by python version from args
# build bwheel
# auditwheel
# upload to pypi/github releases/etc

#!/bin/bash
set -e -u -x

PYTHON_VERSIONS=$1
MANYLINUX_PLATFORM=$2

cp -R /github/workspace /usr/src/tgcalls
cd /usr/src/tgcalls

function repair_wheel {
    wheel="$1"
    if ! auditwheel show "$wheel"; then
        echo "Skipping non-platform wheel $wheel"
    else
        auditwheel repair "$wheel" --plat "$MANYLINUX_PLATFORM" -w /io/wheelhouse/
    fi
}

arrPYTHON_VERSIONS=(${PYTHON_VERSIONS// / })
for PYTHON_VER in "${arrPYTHON_VERSIONS[@]}"; do
    /opt/python/"${PYTHON_VER}"/bin/pip install --upgrade --no-cache-dir pip

    /opt/python/"${PYTHON_VER}"/bin/pip wheel /io/ --no-deps -w wheelhouse/
done

for whl in wheelhouse/*.whl; do
    repair_wheel "$whl"
done

#/opt/python/cp37-cp37m/bin/python setup.py build --debug

# upload to pypi/github releases/etc

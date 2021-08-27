#!/bin/bash
set -e -u -x

PYTHON_VERSIONS=$1
MANYLINUX_PLATFORM=$2

export TWINE_USERNAME=$3
export TWINE_PASSWORD=$4

sudo yum install opencv opencv-devel

cp -R /github/workspace /usr/src/tgcalls
cp -R /usr/src/Libraries/ /tmp/Libraries
cd /usr/src/tgcalls

function repair_wheel {
    wheel="$1"
    if ! auditwheel show "$wheel"; then
        echo "Skipping non-platform wheel $wheel"
    else
        auditwheel repair "$wheel" --plat "$MANYLINUX_PLATFORM" -w wheelhouse/
    fi
}

arrPYTHON_VERSIONS=(${PYTHON_VERSIONS// / })
for PYTHON_VER in "${arrPYTHON_VERSIONS[@]}"; do
    /opt/python/"${PYTHON_VER}"/bin/pip wheel . --no-deps -w wheelhouse/
done

for whl in wheelhouse/*.whl; do
    repair_wheel "$whl"
done

/opt/python/cp37-cp37m/bin/pip install twine
/opt/python/cp37-cp37m/bin/python -m twine upload /usr/src/tgcalls/wheelhouse/*-manylinux*.whl

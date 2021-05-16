#!/bin/bash
set -e -u -x

PYTHON_VERSIONS=$1
MANYLINUX_PLATFORM=$2

function repair_wheel {
    wheel="$1"
    if ! auditwheel show "$wheel"; then
        echo "Skipping non-platform wheel $wheel"
    else
        auditwheel repair "$wheel" --plat "$MANYLINUX_PLATFORM" -w ../dist/
    fi
}

# build
arrPYTHON_VERSIONS=(${PYTHON_VERSIONS// / })
for PYTHON_VER in "${arrPYTHON_VERSIONS[@]}"; do
    /opt/python/"${PYTHON_VER}"/bin/pip wheel . --no-deps -w ../wheelhouse/
done

# repair
for whl in ../wheelhouse/*.whl; do
    repair_wheel "$whl"
done

# test
for PYTHON_VER in "${arrPYTHON_VERSIONS[@]}"; do
    /opt/python/"${PYTHON_VER}"/bin/pip install ../dist/*${PYTHON_VER}*.whl
    /opt/python/"${PYTHON_VER}"/bin/python -c "import tgcalls; tgcalls.ping();"
done

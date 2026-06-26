#!/usr/bin/env sh
set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
cd "$ROOT" || exit 1

if [ -n "${PYTHONPATH:-}" ]; then
    PYTHONPATH="$ROOT/src:$PYTHONPATH"
else
    PYTHONPATH="$ROOT/src"
fi
export PYTHONPATH

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python was not found. Install Python 3.11 or newer and try again."
    if [ -t 0 ]; then
        printf "Press Enter to close..."
        read _answer
    fi
    exit 1
fi

"$PYTHON" -m ualg.gui
status=$?

if [ "$status" -ne 0 ]; then
    echo
    echo "GUI exited with error code $status."
    if [ -t 0 ]; then
        printf "Press Enter to close..."
        read _answer
    fi
fi

exit "$status"

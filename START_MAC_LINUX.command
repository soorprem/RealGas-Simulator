#!/bin/sh
cd "$(dirname "$0")" || exit 1
for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        "$candidate" run.py
        result=$?
        if [ "$result" -ne 0 ]; then
            printf '\nInstall Python 3.11 or 3.12 if needed. Press Enter to close.\n'
            read -r answer
        fi
        exit "$result"
    fi
done
printf 'Please install Python 3.11 or 3.12.\n'
exit 1


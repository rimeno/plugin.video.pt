#!/usr/bin/env sh
set -o errexit

PROGDIR=$(readlink -m "$(dirname "$0")")
readonly PROGDIR

NAME="$(awk -F\" '/^\s*<addon id=/ {print $2}' "${PROGDIR}/addon.xml")"

if test -z "$TMPDIR" ; then
    TMPDIR=/tmp/
fi

cd "$PROGDIR"
VERSION="$(awk -F\" '/^\s*version/ {print $2}' "${PROGDIR}/addon.xml")"
OUTPUT="${TMPDIR}/${NAME}-${VERSION}.zip"

cd "${PROGDIR}/.."
zip -r "$OUTPUT" "$NAME" --exclude \*.git\* \*__pycache__\* \*.buildignore\* \*make\*.sh
echo "→ Addon available at : ${OUTPUT}"

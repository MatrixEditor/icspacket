#!/usr/bin/env bash
#
# Regenerates the C sources/headers, skeletons and Python (.pyi) stubs for
# all icspacket ASN.1 extensions (_iso8823, _mms, _iec61850) using the
# asn1c-bindings compiler (https://github.com/MatrixEditor/asn1c-bindings).
#
# Usage:
#   A1C_PATH=/path/to/asn1c-bindings/asn1c/asn1c \
#   A1C_SKELETONS_PATH=/path/to/asn1c-bindings/skeletons \
#   ./scripts/regen-asn1.sh
#
# Env vars:
#   A1C_PATH             Path to the asn1c-bindings compiler binary.
#                        Defaults to "asn1c" (looked up on PATH).
#   A1C_SKELETONS_PATH   Path to the asn1c-bindings skeletons/ directory.
#                        Required (no sane default exists).
set -euo pipefail

: "${A1C_PATH:=asn1c}"
if [ -z "${A1C_SKELETONS_PATH:-}" ]; then
    echo "error: A1C_SKELETONS_PATH must be set to the asn1c-bindings skeletons/ directory" >&2
    exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTO_DIR="$ROOT_DIR/src/icspacket/proto"
SKELETON_OUT_DIR="$ROOT_DIR/src/icspacket/include/skeletons"

COMMON_FLAGS=(
    -no-gen-example
    -no-gen-autotools
    -fcompound-names
    -Wdebug-compiler
    -S "$A1C_SKELETONS_PATH"
    -out-skeletons="$SKELETON_OUT_DIR"
    -out-skip-imports
    -no-gen-OER
    -no-gen-UPER
    -no-gen-APER
    -no-gen-CBOR
    -no-gen-random-fill
)

# generate <module-name> <extension-src-dir> <asn1-file>...
generate() {
    local name="$1" dir="$2"
    shift 2

    echo "==> Generating ${name} (sources: $*)"
    "$A1C_PATH" "${COMMON_FLAGS[@]}" \
        -M "$name" \
        -out-python-stubs="$(dirname "$dir")" \
        -out-python-sources="$dir" \
        "$@"
}

generate _iso8823 "$PROTO_DIR/iso_pres/_iso8823" \
    "$PROTO_DIR/iso_pres/_iso8823.asn1"

generate _mms "$PROTO_DIR/mms/_mms" \
    "$PROTO_DIR/_acse.asn1" "$PROTO_DIR/mms/_mms.asn1"

generate _iec61850 "$PROTO_DIR/iec61850/_iec61850" \
    "$PROTO_DIR/iec61850/_iec61850.asn1"

echo
echo "Done."

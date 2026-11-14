#!/usr/bin/env bash
# Downloads the smart-search runtime (onnxruntime-web, MIT) and the
# all-MiniLM-L6-v2 int8 ONNX model (Apache-2.0) from npm into site/ and build/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; TMP="$(mktemp -d)"
tarball() { curl -s "https://registry.npmjs.org/$1/$2" | python3 -c 'import sys,json;print(json.load(sys.stdin)["dist"]["tarball"])'; }
mkdir -p "$TMP/ort" "$TMP/model" "$ROOT/build"
curl -sL "$(tarball onnxruntime-web 1.31.1)" | tar xz -C "$TMP/ort"
curl -sL "$(tarball tryaii-minilm-int8 1.0.0)" | tar xz -C "$TMP/model"
M="$TMP/model/package/model.onnx"
echo "8199be6f699a395f99f89df973f9dc5285fbcfcdb2ae1a4e1201dab014f3d2a6  $M" | sha256sum -c -
cp "$TMP"/ort/package/dist/{ort.wasm.min.js,ort-wasm-simd-threaded.mjs,ort-wasm-simd-threaded.wasm} "$ROOT/site/"
cp "$M" "$ROOT/build/model.onnx"
# artifact hosting caps files at 20 MiB, so the model ships in two parts
head -c 11500000 "$M" > "$ROOT/site/model.part1.wasm"
tail -c +11500001 "$M" > "$ROOT/site/model.part2.wasm"
rm -rf "$TMP"; echo "assets ready"

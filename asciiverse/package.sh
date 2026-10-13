#!/bin/sh
# Packs each game built by build.sh into its own archive for av:
# dist/<id>-<target>.tar.gz, with the binary at the top beside its man
# page, the collection's LICENSE and README.md, and the game's own LICENSE
# where it has one. hangman also gets its word list (asciiverse/hangman).
#
#   asciiverse/package.sh x86_64-unknown-linux-musl
set -eu
cd "$(dirname "$0")/.."
target="$1"
mkdir -p dist
grep -v '^#' asciiverse/games.txt | while read -r id prog; do
  [ -n "$id" ] || continue
  stage="stage/$id"
  rm -rf "$stage" && mkdir -p "$stage"
  cp "out/$prog" "$prog/$prog.6" LICENSE README.md "$stage/"
  [ -f "$prog/LICENSE" ] && cp "$prog/LICENSE" "$stage/LICENSE.$prog"
  [ -d "asciiverse/$prog" ] && cp "asciiverse/$prog/"* "$stage/"
  tar -czf "dist/$id-$target.tar.gz" -C "$stage" .
done
ls dist

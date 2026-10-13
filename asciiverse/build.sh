#!/bin/sh
# Builds the games in asciiverse/games.txt into out/, with upstream's
# configure and Makefile. The curses library and extra flags come from the
# environment, so one script serves every target
# (see .github/workflows/release.yml):
#
#   asciiverse/build.sh                                       # Debian, Ubuntu
#   LIBS=-lncursesw LDFLAGS=-static asciiverse/build.sh       # Alpine, static
#   LIBS=-lncurses CFLAGS="-arch arm64" LDFLAGS="-arch arm64" asciiverse/build.sh  # macOS
#
# configure reads the version with git, so git must be installed.
# Upstream links -lncurses, which on Debian and Ubuntu is the narrow
# library without the wide-character calls the shared UI code uses.
set -eu
cd "$(dirname "$0")/.."
LIBS="${LIBS:--lncursesw -ltinfo}"
CFLAGS="${CFLAGS:-}"
./configure --prefix=/usr >/dev/null
# .o is upstream's link to the build folder; a stale one points elsewhere
rm -rf out .o && mkdir -p out
make -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)" \
  builddir="$PWD/out/build" libs="$LIBS" CFLAGS="-Wall -Wextra $CFLAGS"
grep -v '^#' asciiverse/games.txt | while read -r id prog; do
  [ -n "$id" ] || continue
  cp "out/build/$prog/$prog" "out/$prog"
  echo "built $prog"
done

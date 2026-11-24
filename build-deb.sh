#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
set -eu
cd "$(dirname "$0")"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT HUP INT TERM
install -Dm755 gallery.py "$stage/usr/bin/jatayu-gallery"
install -Dm644 jatayu-gallery.png "$stage/usr/share/icons/hicolor/128x128/apps/jatayu-gallery.png"
install -Dm644 jatayu-gallery.desktop "$stage/usr/share/applications/jatayu-gallery.desktop"
install -Dm644 README.md "$stage/usr/share/doc/jatayu-gallery/README.md"
install -Dm644 copyright "$stage/usr/share/doc/jatayu-gallery/copyright"
mkdir -p "$stage/DEBIAN"
cat > "$stage/DEBIAN/control" <<'CONTROL'
Package: jatayu-gallery
Version: 0.4.0-1
Architecture: all
Maintainer: JatayuOS
Depends: python3 (>= 3.11), python3-pyqt5, python3-pil (>= 9.1)
Section: graphics
Priority: optional
Homepage: https://jatayuos.in
Description: Image viewer and editor for JatayuOS
 Browse local photographs, make basic edits, and export a separate copy.
CONTROL
dpkg-deb --root-owner-group --build "$stage" ../jatayu-gallery_0.4.0-1_all.deb

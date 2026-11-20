#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "$0")" && pwd)
assets="$here/../../../.cache/pr_data"
mkdir -p "$assets"
fetch() {
    local name=$1 sha=$2 url=$3
    if [[ -f "$assets/$name" ]] && echo "$sha  $assets/$name" | sha256sum -c --status; then return; fi
    curl --retry 2 -LfsS -H 'Accept: application/vnd.github.raw+json' "$url" -o "$assets/$name.part"
    echo "$sha  $assets/$name.part" | sha256sum -c
    mv "$assets/$name.part" "$assets/$name"
}
fetch ne.shp 7ce119ef6342e43cff7c0c3004e0911ab7ec1988a14734372031d2012180e7bc 'https://api.github.com/repos/nvkelso/natural-earth-vector/git/blobs/a10056b74ef4ba38e4af7f7f127ea8f48124b2da'
fetch pr.zip df6d3e05984d5e041656dc69b7e40a41f5dbf7ce233c8534fc9754a289ac27a3 'https://codeload.github.com/johnpoole/PointRobertsOceanView/zip/1a4a328a1dc642cf82ac691116fcd2cd1ca5a77e'
fetch Manrope.ttf 3ae11c49db0455a3cc33e37d380f20fdb8c7f8b41dc07625c177e3d87a9d6ae6 'https://api.github.com/repos/google/fonts/git/blobs/75274da58537d6123b14f2cd0c355ad4681fc2b3'

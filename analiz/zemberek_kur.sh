#!/usr/bin/env bash
#
# Zemberek sanal ortamini (zemberek_env) sifirdan kurar.
#
# zemberek-python, antlr4-python3-runtime 4.8 surumune ihtiyac duyar; bu surum
# yeni Python'larda (3.12+) pip ile kurulamiyor ("typing.io" hatasi). Bu
# script 4.8'in kaynak kodunu indirip tek satirlik uyumluluk duzeltmesini
# yapar ve sanal ortama kopyalar.
#
# TR-LLM-Analiz reposundaki (tez) ayni script'in kopyasi.
#
# Kullanim (analiz klasorunde):
#   bash zemberek_kur.sh
# Sonra:
#   zemberek_env/bin/python3 ek_siklik.py

set -euo pipefail
cd "$(dirname "$0")"

ORTAM="zemberek_env"
GECICI="$(mktemp -d)"
trap 'rm -rf "$GECICI"' EXIT

if [[ -e "$ORTAM" ]]; then
  YEDEK="${ORTAM}_eski_$(date +%Y%m%d_%H%M%S)"
  echo "Mevcut $ORTAM calismiyor olabilir; silinmeden $YEDEK olarak yedekleniyor."
  mv "$ORTAM" "$YEDEK"
fi

echo "[1/4] Sanal ortam olusturuluyor: $ORTAM"
python3 -m venv "$ORTAM"
PY="$ORTAM/bin/python3"
"$PY" -m pip install -q --upgrade pip

echo "[2/4] Paketler kuruluyor (numpy, scipy, zemberek-python)"
# zemberek-python pkg_resources kullaniyor; setuptools 81+ bunu kaldirdi
"$PY" -m pip install -q numpy scipy "setuptools<81"
"$PY" -m pip install -q --no-deps zemberek-python

echo "[3/4] antlr4 4.8 indirilip yeni Python icin duzeltiliyor"
"$PY" -m pip download -q --no-deps --no-binary :all: "antlr4-python3-runtime==4.8" -d "$GECICI"
tar xzf "$GECICI"/antlr4-python3-runtime-4.8.tar.gz -C "$GECICI"
grep -rl "typing.io" "$GECICI/antlr4-python3-runtime-4.8/src" \
  | xargs sed -i 's/from typing.io import TextIO/from typing import TextIO/'
SITE="$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
rm -rf "$SITE/antlr4"
cp -r "$GECICI/antlr4-python3-runtime-4.8/src/antlr4" "$SITE/"

echo "[4/4] Test ediliyor"
"$PY" - <<'EOF'
from zemberek import TurkishMorphology
m = TurkishMorphology.create_with_defaults()
a = m.analyze("kitaplarımızdan").analysis_results[0]
print("Zemberek calisiyor:", a.format_string())
EOF

echo
echo "Kurulum tamam. Ek analizini calistirmak icin:"
echo "  zemberek_env/bin/python3 ek_siklik.py"

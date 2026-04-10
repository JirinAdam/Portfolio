"""
Stáhne Inter fonty (v3.19) do data/fonts/. Spustit jednou.
Inter v4+ používá variable font — v3.19 jsou poslední s oddělenými weight TTF.
"""
import io
import ssl
import urllib.request
import zipfile
from pathlib import Path

FONTS_DIR = Path(__file__).parent.parent / "data" / "fonts"
FONTS_DIR.mkdir(parents=True, exist_ok=True)

ZIP_URL = "https://github.com/rsms/inter/releases/download/v3.19/Inter-3.19.zip"
TARGETS = ["Inter-Light.ttf", "Inter-Regular.ttf", "Inter-SemiBold.ttf", "Inter-ExtraBold.ttf"]

ctx = ssl._create_unverified_context()

print(f"Stahuji Inter-3.19.zip...")
resp = urllib.request.urlopen(ZIP_URL, context=ctx)
zf = zipfile.ZipFile(io.BytesIO(resp.read()))

for name in TARGETS:
    target = FONTS_DIR / name
    if target.exists():
        print(f"  Existuje: {name}")
        continue
    # Najít soubor v ZIP (může být ve složce)
    matches = [n for n in zf.namelist() if n.endswith(name)]
    if not matches:
        print(f"  CHYBA: {name} nenalezen v ZIP. Obsah: {zf.namelist()[:10]}")
        continue
    target.write_bytes(zf.read(matches[0]))
    print(f"  OK: {target}")

print("Hotovo.")

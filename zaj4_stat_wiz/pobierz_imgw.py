"""Pobiera dobowe dane synoptyczne IMGW-PIB dla stacji Łódź-Lublinek i Warszawa-Okęcie.

Źródło: https://danepubliczne.imgw.pl, katalog dane_meteorologiczne/dobowe/synop
Układ plików na serwerze:
  lata < 2001  -> katalogi pięcioletnie, np. 1991_1995/1991_1995_465_s.zip
  lata >= 2001 -> katalogi roczne,       np. 2010/2010_465_s.zip
W archiwum: s_d_<kod>_<okres>.csv (bez nagłówka, cp1250) oraz s_d_t_... (pomijany).
Opis kolumn: dobowe/synop/s_d_format.txt

Użycie:
  python pobierz_imgw.py                  # 1991-2023
  python pobierz_imgw.py --od 2001 --do 2020
"""

import argparse
import io
import logging
import re
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE = ("https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
        "dane_meteorologiczne/dobowe/synop")
STACJE = {"465": "Łódź-Lublinek", "375": "Warszawa-Okęcie"}

# Pierwsze 18 kolumn wg s_d_format.txt (dalsze kolumny pomijamy)
KOLUMNY = ["kod", "nazwa", "rok", "mies", "dzien",
           "tmax", "w_tmax", "tmin", "w_tmin", "tmean", "w_tmean",
           "tmin_grunt", "w_tmin_grunt", "opad", "w_opad",
           "rodzaj_opadu", "snieg", "w_snieg"]
POMIARY = ["tmax", "tmin", "tmean", "tmin_grunt", "opad", "snieg"]


def katalogi(od: int, do: int) -> list[str]:
    """Nazwy katalogów IMGW pokrywające lata od..do."""
    wynik = []
    for rok in range(od, do + 1):
        if rok >= 2001:
            nazwa = str(rok)
        elif rok <= 1965:
            nazwa = "1960_1965"
        else:
            start = rok - (rok - 1966) % 5
            nazwa = f"{start}_{start + 4}"
        if nazwa not in wynik:
            wynik.append(nazwa)
    return wynik


def pobierz_zip(sesja: requests.Session, katalog: str, kod: str, cache: Path) -> bytes:
    """Pobiera archiwum (lub bierze je z cache). Gdy nazwa nie pasuje do wzorca,
    szuka jej w listingu katalogu."""
    plik = cache / f"{katalog}_{kod}_s.zip"
    if plik.exists():
        return plik.read_bytes()

    url = f"{BASE}/{katalog}/{katalog}_{kod}_s.zip"
    r = sesja.get(url, timeout=60)
    if r.status_code == 404:
        listing = sesja.get(f"{BASE}/{katalog}/", timeout=60).text
        m = re.search(rf'href="([^"]*_{kod}_s\.zip)"', listing)
        if m is None:
            raise FileNotFoundError(f"Brak archiwum stacji {kod} w katalogu {katalog}")
        url = f"{BASE}/{katalog}/{m.group(1)}"
        r = sesja.get(url, timeout=60)
    r.raise_for_status()

    plik.write_bytes(r.content)
    logger.info("Pobrano %s", url)
    time.sleep(0.5)  # nie obciążamy serwera IMGW
    return r.content


def wczytaj_s_d(zawartosc: bytes) -> pd.DataFrame:
    """Czyta plik s_d_*.csv z archiwum i zamienia kody statusu na wartości."""
    with zipfile.ZipFile(io.BytesIO(zawartosc)) as z:
        nazwy = [n for n in z.namelist() if re.match(r"s_d_\d", Path(n).name)]
        if len(nazwy) != 1:
            raise ValueError(f"Oczekiwano jednego pliku s_d_*, znaleziono: {z.namelist()}")
        with z.open(nazwy[0]) as f:
            df = pd.read_csv(f, header=None, encoding="cp1250",
                             usecols=range(len(KOLUMNY)), names=KOLUMNY,
                             dtype={k: str for k in KOLUMNY if k.startswith("w_")}
                                   | {"kod": str})

    for kol in POMIARY:
        status = df[f"w_{kol}"].fillna("").str.strip()
        df.loc[status == "8", kol] = float("nan")      # 8 = brak pomiaru
        if kol in ("opad", "snieg"):
            df.loc[status == "9", kol] = 0.0           # 9 = brak zjawiska

    df["data"] = pd.to_datetime(dict(year=df["rok"], month=df["mies"], day=df["dzien"]))
    return df[["data", "kod", *POMIARY]]


def raport(df: pd.DataFrame, od: int, do: int) -> None:
    """Kompletność i spójność danych, zanim trafią na zajęcia."""
    wszystkie_dni = pd.date_range(f"{od}-01-01", f"{do}-12-31")
    for stacja, g in df.groupby("stacja"):
        brak_dni = len(wszystkie_dni.difference(g["data"]))
        braki = (g[POMIARY].isna().mean() * 100).round(1).to_dict()
        logger.info("%s: %d dni, brakujących dni: %d, braki wartości [%%]: %s",
                    stacja, len(g), brak_dni, braki)

    dup = df.duplicated(["stacja", "data"]).sum()
    niespojne = df.query("tmin > tmean or tmean > tmax")
    if dup:
        logger.warning("Zduplikowane wiersze (stacja, data): %d", dup)
    if len(niespojne):
        logger.warning("Wiersze z tmin > tmean lub tmean > tmax: %d", len(niespojne))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--od", type=int, default=1991)
    p.add_argument("--do", type=int, default=2023)
    p.add_argument("--katalog", type=Path, default=Path("dane_imgw"))
    a = p.parse_args()

    cache = a.katalog / "surowe"
    cache.mkdir(parents=True, exist_ok=True)

    czesci = []
    with requests.Session() as sesja:
        for kod, stacja in STACJE.items():
            for kat in katalogi(a.od, a.do):
                df = wczytaj_s_d(pobierz_zip(sesja, kat, kod, cache))
                czesci.append(df.assign(stacja=stacja))

    dane = (pd.concat(czesci, ignore_index=True)
              .query("@a.od <= data.dt.year <= @a.do")
              .sort_values(["stacja", "data"])
              .reset_index(drop=True))
    dane = dane[["data", "stacja", *POMIARY]]

    raport(dane, a.od, a.do)

    wyjscie = a.katalog / f"lodz_warszawa_{a.od}_{a.do}"
    dane.to_csv(wyjscie.with_suffix(".csv"), index=False)
    try:
        dane.to_parquet(wyjscie.with_suffix(".parquet"), index=False)
    except ImportError:
        logger.info("Brak pyarrow — zapisano tylko CSV")
    logger.info("Zapisano %d wierszy do %s.*", len(dane), wyjscie)


if __name__ == "__main__":
    main()

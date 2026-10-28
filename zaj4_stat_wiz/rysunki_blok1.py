"""Rysunki do slajdów bloku 1 (statystyka).

Uruchom w katalogu, w którym leży dane_imgw/lodz_warszawa_1991_2023.csv:
    python rysunki_blok1.py
Rysunki trafiają do katalogu rysunki/.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

DANE = Path("dane_imgw/lodz_warszawa_1991_2024.csv")
WYNIKI = Path("rysunki")
ROK = "2020"                                   # rok pokazywany na wykresach dziennych

LODZ, WAW = "Łódź-Lublinek", "Warszawa-Okęcie"
KOLOR = {LODZ: "#0072B2", WAW: "#E69F00"}
SEZONY = {12: "zima", 1: "zima", 2: "zima", 3: "wiosna", 4: "wiosna", 5: "wiosna",
          6: "lato", 7: "lato", 8: "lato", 9: "jesień", 10: "jesień", 11: "jesień"}
CM = 1 / 2.54

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "figure.constrained_layout.use": True})
WYNIKI.mkdir(exist_ok=True)

# Dane: jedna kolumna na stację, różnica dla każdego dnia
df = pd.read_csv(DANE, parse_dates=["data"])
szer = df.pivot(index="data", columns="stacja", values="tmean").dropna()
szer["roznica"] = szer[LODZ] - szer[WAW]
szer["sezon"] = pd.Categorical(szer.index.month.map(SEZONY),
                               ["zima", "wiosna", "lato", "jesień"])

# 1. Pomiary w parach: temperatura obu stacji i różnica w jednym roku
rok = szer.loc[ROK]
fig, (gora, dol) = plt.subplots(2, 1, figsize=(16 * CM, 9 * CM), sharex=True)
for stacja in (LODZ, WAW):
    gora.plot(rok.index, rok[stacja], color=KOLOR[stacja], lw=1, label=stacja)
gora.set_ylabel("temperatura [°C]")
gora.legend(loc="upper left")
dol.plot(rok.index, rok["roznica"], color="gray", lw=0.8)
dol.axhline(0, color="k", lw=0.6)
dol.set_ylabel("Łódź − Warszawa [°C]")
fig.savefig(WYNIKI / "pary.png", dpi=200)

# 2. Rozkład różnic dobowych i dopasowany rozkład normalny
srednia, odchylenie = stats.norm.fit(szer["roznica"])
x = np.linspace(-5, 5, 300)
fig, ax = plt.subplots(figsize=(13 * CM, 8 * CM))
ax.hist(szer["roznica"], bins=np.arange(-5, 5.01, 0.2), density=True,
        color="#9DB4CF", edgecolor="white", label="dane: wszystkie dni")
ax.plot(x, stats.norm.pdf(x, srednia, odchylenie), color="#C0392B", lw=2,
        label=f"rozkład normalny: średnia {srednia:.2f} °C")
ax.axvline(0, color="k", lw=0.8)
ax.set(xlim=(-5, 5), xlabel="różnica Łódź − Warszawa w jednym dniu [°C]",
       ylabel="gęstość")
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0))
fig.savefig(WYNIKI / "rozklad.png", dpi=200)

# 3. Diagnostyka reszt modelu roznica ~ C(sezon)
model = smf.ols("roznica ~ C(sezon)", data=szer).fit()
reszty = model.resid
fig, (lewy, prawy) = plt.subplots(1, 2, figsize=(17 * CM, 7 * CM))
lewy.hist(reszty, bins=np.arange(-5, 5.01, 0.25), color="#9DB4CF", edgecolor="white")
lewy.axvline(0, color="k", lw=0.8)
lewy.set(xlim=(-5, 5), xlabel="reszta [°C]", ylabel="liczba dni",
         title="rozkład reszt")
prawy.plot(reszty.loc[ROK].index, reszty.loc[ROK], color="gray", lw=0.8)
prawy.axhline(0, color="k", lw=0.6)
prawy.set(ylabel="reszta [°C]", title=f"reszty dzień po dniu, rok {ROK}")
prawy.xaxis.set_major_formatter(mdates.DateFormatter("%m.%Y"))
prawy.tick_params(axis="x", labelrotation=30)
fig.savefig(WYNIKI / "reszty.png", dpi=200)

print("Zapisano: pary.png, rozklad.png, reszty.png w katalogu", WYNIKI)

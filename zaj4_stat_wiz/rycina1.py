"""Rycina 1: różnica temperatury Łódź − Warszawa, 1991–2023.

Uruchomienie (w katalogu projektu):
    python rycina1.py

Wejście:  dane_imgw/lodz_warszawa_1991_2023.csv   (tworzy go pobierz_imgw.py)
Wyjście:  ryciny/rycina1.pdf oraz ryciny/rycina1.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# ---- 1. Ustawienia: wszystko, co można zmienić, w jednym miejscu ----------
DANE = Path("dane_imgw/lodz_warszawa_1991_2024.csv")
WYNIKI = Path("ryciny")
STYL = Path(__file__).with_name("publikacja.mplstyle")

MM = 1 / 25.4                      # matplotlib liczy rozmiar w calach
SZEROKOSC = 180 * MM               # cała strona czasopisma
WYSOKOSC = 120 * MM

LODZ, WAW = "Łódź-Lublinek", "Warszawa-Okęcie"
PALETA = {LODZ: "#0072B2", WAW: "#E69F00"}          # paleta Okabe-Ito
SEZONY = {12: "zima", 1: "zima", 2: "zima", 3: "wiosna", 4: "wiosna", 5: "wiosna",
          6: "lato", 7: "lato", 8: "lato", 9: "jesień", 10: "jesień", 11: "jesień"}
KOLEJNOSC = ["zima", "wiosna", "lato", "jesień"]
MIESIACE = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


# ---- 2. Dane: wczytanie i przygotowanie, bez rysowania --------------------
def wczytaj(sciezka=DANE):
    df = pd.read_csv(sciezka, parse_dates=["data"])
    szer = df.pivot(index="data", columns="stacja", values="tmean").dropna()
    szer["roznica"] = szer[LODZ] - szer[WAW]
    szer["sezon"] = pd.Categorical(szer.index.month.map(SEZONY), KOLEJNOSC, ordered=True)
    return df, szer


# ---- 3. Panele: każda funkcja rysuje w podanym ax i go zwraca -------------
def mapa_ciepla(szer, ax):
    tab = szer["roznica"].groupby([szer.index.month, szer.index.year]).mean().unstack()
    zakres = np.nanmax(np.abs(tab.to_numpy()))          # skala symetryczna wokół zera
    sns.heatmap(tab, cmap="RdBu_r", center=0, vmin=-zakres, vmax=zakres, ax=ax,
                xticklabels=5, cbar_kws={"label": "Łódź − Warszawa [°C]"})
    ax.set_yticks(np.arange(12) + 0.5, MIESIACE, rotation=0)
    ax.set(xlabel="", ylabel="miesiąc")
    return ax


def pudelka_roznicy(szer, ax):
    sns.boxplot(data=szer, x="sezon", y="roznica", color="#9DB4CF",
                fliersize=0.6, linewidth=0.6, ax=ax)
    ax.axhline(0, color="k", lw=0.6)
    ax.set(xlabel="", ylabel="Łódź − Warszawa [°C]")
    return ax


def trend_roczny(df, ax):
    roczne = df.groupby(["stacja", df["data"].dt.year.rename("rok")])["tmean"].mean()
    for stacja, seria in roczne.groupby(level="stacja"):
        lata = seria.index.get_level_values("rok")
        ax.plot(lata, seria, "o-", ms=2, color=PALETA[stacja], label=stacja)
        a, b = np.polyfit(lata, seria, 1)
        ax.plot(lata, a * lata + b, "--", color=PALETA[stacja], lw=0.8)
    ax.set(xlabel="", ylabel="średnia roczna temperatura [°C]")
    ax.legend()
    return ax


# ---- 4. Rycina: układ paneli i podpisy -----------------------------------
def rycina(df, szer):
    fig, axd = plt.subplot_mosaic([["a", "a"], ["b", "c"]],
                                  figsize=(SZEROKOSC, WYSOKOSC), height_ratios=[1, 1.1])
    mapa_ciepla(szer, axd["a"])
    pudelka_roznicy(szer, axd["b"])
    trend_roczny(df, axd["c"])
    for litera, ax in axd.items():
        ax.set_title(f"({litera})", loc="left", fontweight="bold")
    return fig


# ---- 5. Uruchomienie: wczytaj, narysuj, zapisz ---------------------------
def main():
    plt.style.use(STYL)
    df, szer = wczytaj()
    fig = rycina(df, szer)
    WYNIKI.mkdir(exist_ok=True)
    fig.savefig(WYNIKI / "rycina1.pdf")                 # dla czasopisma
    fig.savefig(WYNIKI / "rycina1.png", dpi=300)        # do podglądu i prezentacji
    print("zapisano", WYNIKI / "rycina1.pdf")


if __name__ == "__main__":
    main()

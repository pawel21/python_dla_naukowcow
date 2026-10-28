# Jak przygotować środowisko do zajęć 4

Potrzebny jest Python 3.10 lub nowszy. Wszystkie polecenia wpisujemy w terminalu, w głównym katalogu projektu.

## 0. Sprawdź wersję Pythona

```bash
python --version
```

Jeśli wynik jest niższy niż 3.10 (na przykład `Python 3.8.10`), zainstaluj nowszego Pythona ze strony python.org — stary możesz zostawić, nie trzeba go usuwać.

## 1. Utwórz środowisko — z właściwą wersją Pythona

| System | Polecenie |
|---|---|
| Windows | `py -3.12 -m venv .venv` |
| Linux, macOS | `python3.12 -m venv .venv` |

Zamiast 3.12 wpisz wersję, którą masz zainstalowaną (3.10 lub nowszą). Na Windows `py --list` pokazuje wszystkie zainstalowane wersje.

Jeśli wcześniej powstał katalog `.venv` ze starym Pythonem, najpierw go usuń.

## 2. Włącz środowisko

| System | Polecenie |
|---|---|
| Windows, PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows, Git Bash | `source .venv/Scripts/activate` |
| Linux, macOS | `source .venv/bin/activate` |

Na początku wiersza terminala pojawi się `(.venv)`.

Jeśli PowerShell odmówi uruchomienia skryptu, wpisz raz:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 3. Zainstaluj biblioteki

```bash
pip install -r requirements.txt
```

## 4. Sprawdź środowisko

```bash
python pobierz_imgw.py
python sprawdz_srodowisko.py
```

Na końcu powinno pojawić się: `Wszystko gotowe.`

## 5. Otwórz notebook

```bash
jupyter lab zajecia4_ekosystem.ipynb
```

W Visual Studio Code: otwórz notebook i w prawym górnym rogu wybierz jądro z katalogu `.venv`.

## Najczęstszy błąd

`Could not find a version that satisfies the requirement scipy>=1.11` oznacza, że środowisko powstało ze zbyt starego Pythona (3.8 lub 3.9). Usuń katalog `.venv` i wróć do kroku 1.

## Alternatywa: conda

```bash
conda env create -f environment.yml
conda activate zajecia4
```

Dalej kroki 4 i 5 bez zmian.

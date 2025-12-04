# FolderComparator

Narzędzie do porównywania folderów wykorzystujące Beyond Compare 5.

## Opis

Skrypt automatyzuje proces porównywania dwóch folderów i generuje raport z różnicami. Wykorzystuje Beyond Compare do analizy i Python do przetwarzania wyników.

## Wymagania

- Python 3.x
- Beyond Compare 5
- Pakiet `colorama` (instalowany automatycznie)

## Użycie

### Bezpośrednio z Python

```bash
python check_report.py -c <ścieżka_do_folderu_porównania>
```

### Z FreeCommander (zalecane)

Użyj pliku `run_check.bat`:

```bash
run_check.bat "C:\path\to\folder"
```

### Konfiguracja w FreeCommander

- **Program**: `C:\.Github\Tools\FolderComparator\run_check.bat`
- **Parametr**: `"%RightDir%"` (lub dowolna ścieżka)

### Przykład

```bash
python check_report.py -c "C:\temp\results\folder_do_porownania"
```

## Funkcjonalność

- Automatyczne tworzenie skryptu Beyond Compare (`script_upd.txt`)
- Porównanie folderu wzorca z podanym folderem
- Kolorowe wyświetlanie wyników:
  - 🔴 **Czerwony** - różnice (brakujące, nowe, zmienione pliki)
  - 🟢 **Zielony** - brak różnic
- Logowanie wyników do `log.log`
- Formatowanie raportu z polskimi etykietami
- Oczekiwanie na Enter przed zakończeniem

## Pliki

- `check_report.py` - główny skrypt Python
- `run_check.bat` - plik batch do uruchamiania z FreeCommander
- `script.txt` - szablon skryptu Beyond Compare
- `script_upd.txt` - wygenerowany skrypt z ścieżkami
- `__report.txt` - raport z Beyond Compare
- `log.log` - historia porównań

## Wyniki

Skrypt wyświetla:

- **Brakujące pliki** - pliki obecne tylko w folderze wzorca
- **Nowe pliki** - pliki obecne tylko w porównywanym folderze  
- **Pliki różne** - pliki o różnej zawartości

# PC State Snapshot & Diff

**Rendszerprogramozás – beadandó projekt**

A **PC State Snapshot & Diff** egy Windows 11-re készült parancssoros eszköz, amely a számítógép kiválasztott állapotáról JSON pillanatfelvételt készít, majd két állapot között megmutatja a változásokat.

A cél egy egyszerű, reprodukálható folyamat:

```text
snapshot → snapshot → diff → JSON report
```

## Fő funkciók

- rendszer-, CPU-, RAM- és lemezinformációk gyűjtése
- hálózati adapterek, IPv4, gateway és DNS mentése
- kiválasztott Windows szolgáltatások mentése
- futó folyamatok mentése
- figyelő TCP portok mentése
- snapshotok JSON formátumban
- két snapshot összehasonlítása
- színes diff kimenet: zöld = új, piros = eltűnt, sárga = módosult
- legutóbbi két snapshot gyors összehasonlítása `diff --latest` paranccsal
- JSON diff riport
- ZIP backup és restore
- `--dry-run` előnézet restore és cleanup előtt
- régi snapshotok takarítása
- naplózás
- CLI súgó minden parancshoz

## Fontos biztonsági korlátozás

A program **nem módosítja a Windows rendszerbeállításait**. Nem állít le szolgáltatásokat, nem módosít hálózati konfigurációt és nem változtat rendszerfájlokat.

A `restore` és `cleanup` kizárólag a projekt saját `snapshots/` fájljait kezeli.

## Követelmények

- Windows 11
- Python 3.11 vagy újabb
- internetkapcsolat az első telepítéskor a `psutil` telepítéséhez

## Telepítés ZIP-ből

1. Csomagold ki a projektet.
2. Nyiss PowerShellt a projekt mappájában.
3. Futtasd:

```powershell
.\start.bat
```

A `start.bat` létrehozza a `.venv` virtuális környezetet és telepíti a szükséges függőséget.

Ezután a programot a mellékelt launcherrel lehet használni:

```powershell
.\sysnapshot --help
```

**Nem kell minden alkalommal ezt gépelni:**

```text
.\.venv\Scripts\python.exe run.py ...
```

A `sysnapshot.bat` ezt automatikusan kezeli.

## Gyors használat

```powershell
.\sysnapshot snapshot
.\sysnapshot list
.\sysnapshot show <SNAPSHOT_ID>
.\sysnapshot diff <OLD_ID> <NEW_ID>
.\sysnapshot diff --latest
.\sysnapshot backup
.\sysnapshot restore <ARCHIVE>
.\sysnapshot cleanup --keep 10
```

A részletes súgó bármely parancshoz elérhető:

```powershell
.\sysnapshot --help
.\sysnapshot snapshot --help
.\sysnapshot show --help
.\sysnapshot diff --help
.\sysnapshot restore --help
.\sysnapshot cleanup --help
```

## Parancsok

### `snapshot`

Új PC-állapotot ment JSON fájlba.

```powershell
.\sysnapshot snapshot
```

A program kiírja az új snapshot ID-ját, például:

```text
Snapshot created successfully.
ID:   20261006-225409-274095
File: ...\snapshots\20261006-225409-274095.json
```

### `list`

Kilistázza a rendelkezésre álló snapshotokat.

```powershell
.\sysnapshot list
```

Az itt megjelenő ID-t lehet használni a `show` és `diff` parancsoknál.

### `show <SNAPSHOT_ID>`

Egy konkrét snapshot tartalmát jeleníti meg.

```powershell
.\sysnapshot show 20261006-225409-274095
```

A `<SNAPSHOT_ID>` helyére mindig a `list` által megjelenített tényleges ID kerül.

### `diff <OLD_ID> <NEW_ID>`

Két snapshot összehasonlítása.

```powershell
.\sysnapshot diff 20261006-225409-274095 20261006-225534-684683
```

A paraméterek sorrendje:

```text
OLD_ID = régebbi snapshot
NEW_ID = újabb snapshot
```

A kimenet színei:

- 🟢 **ADDED** – új elem
- 🔴 **REMOVED** – eltűnt elem
- 🟡 **CHANGED** – megváltozott érték

A program JSON riportot is készít a `reports/` mappába.

### `diff --latest`

A legegyszerűbb diff használat: automatikusan összehasonlítja a két legújabb snapshotot.

```powershell
.\sysnapshot diff --latest
```

Ez különösen hasznos a normál munkafolyamatban:

```powershell
.\sysnapshot snapshot
.\sysnapshot diff --latest
```

A `--latest` mellett nem kell ID-kat megadni.

### `diff --no-color`

Kikapcsolja a színes terminálkimenetet.

```powershell
.\sysnapshot diff OLD_ID NEW_ID --no-color
```

Ez akkor hasznos, ha a kimenetet fájlba másoljuk, vagy olyan terminált használunk, amely nem kezeli a színeket.

### `backup`

Az összes jelenlegi snapshotot ZIP archívumba menti.

```powershell
.\sysnapshot backup
```

A ZIP a `backups/` mappába kerül.

### `restore <ARCHIVE>`

Egy korábbi snapshot ZIP tartalmát visszaállítja a `snapshots/` mappába.

```powershell
.\sysnapshot restore .\backups\snapshots-20261006-225728.zip
```

### `restore <ARCHIVE> --dry-run`

A tényleges módosítás előtt ellenőrizhető, hogy mit állítana vissza.

```powershell
.\sysnapshot restore .\backups\snapshots-20261006-225728.zip --dry-run
```

A dry-run **nem módosít fájlokat**.

### `cleanup --keep N`

Csak a legújabb `N` snapshotot tartja meg, a régebbieket törli.

Először mindig érdemes előnézetet készíteni:

```powershell
.\sysnapshot cleanup --keep 10 --dry-run
```

Ha az eredmény megfelelő:

```powershell
.\sysnapshot cleanup --keep 10
```

### `cleanup --dry-run`

A dry-run csak megmutatja, mely fájlokat törölné, de nem töröl semmit.

## Tipikus munkafolyamat

Egy változtatás előtti és utáni állapot összehasonlítása:

```powershell
.\sysnapshot snapshot
```

Ezután elvégezhető a vizsgált változtatás.

Majd:

```powershell
.\sysnapshot snapshot
.\sysnapshot diff --latest
```

Ha szükséges, a részletes JSON eredmény a `reports/` mappában megtalálható.

## Mappaszerkezet

```text
pc-state-snapshot-diff/
├── src/                 # programkód
│   ├── collectors/      # rendszeradat-gyűjtők
│   ├── main.py          # CLI és parancsok
│   ├── diff.py          # összehasonlítás
│   ├── storage.py       # mentés, backup, restore, cleanup
│   └── config.py        # konfiguráció
├── config/              # konfigurációs fájl
├── snapshots/           # JSON snapshotok
├── reports/             # JSON diff riportok
├── logs/                # naplófájlok
├── backups/             # ZIP mentések
├── tests/               # tesztek
├── run.py               # Python belépési pont
├── sysnapshot.bat       # egyszerű Windows CLI launcher
├── start.bat            # telepítés / előkészítés
├── requirements.txt     # külső függőségek
├── .gitignore           # Gitből kizárt generált fájlok
└── README.md            # teljes dokumentáció
```

## Tesztelés

A diff motorhoz külső tesztfüggőség nélküli teszt tartozik.

```powershell
.\.venv\Scripts\python.exe tests\test_diff.py
```

Sikeres futás esetén:

```text
All tests passed.
```

A manuálisan ellenőrzött fő funkciók:

- snapshot készítés
- snapshot lista
- snapshot megtekintés
- diff
- JSON riport
- backup
- restore dry-run
- cleanup dry-run

## GitHub

A projekt GitHub repositoryként is használható. A generált snapshotok, riportok, logok, ZIP backupok és a `.venv` szándékosan ki vannak zárva a Gitből.

Első feltöltés:

```powershell
git init
git add .
git status
git commit -m "Initial project version"
git branch -M main
git remote add origin https://github.com/SAJAT-FELHASZNALO/pc-state-snapshot-diff.git
git push -u origin main
```

A `git status` segítségével ellenőrizhető, hogy ne kerüljenek fel személyes/generált snapshotok.

## Exit code-ok

- `0` – sikeres művelet / nincs változás
- `1` – a `diff` változást talált
- `2` – általános futási hiba
- `3` – bemeneti, konfigurációs vagy platformhiba
- `130` – felhasználói megszakítás

## Konfiguráció

A működés a `config/config.json` fájlból szabályozható. Itt állítható például, hogy mely adatcsoportokat gyűjtse a program, mely folyamatokat hagyja figyelmen kívül, illetve mely Windows szolgáltatásokat figyelje.

A projekt Windows 11-re készült.

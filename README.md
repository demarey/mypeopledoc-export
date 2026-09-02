# MyPeopleDoc Export

Exports your MyPeopleDoc documents and sorts them locally by **type** and **year**:

```
Documents_MyPeopleDoc/
├── Bulletin de paie/
│   ├── 2024/
│   └── 2025/
├── Contrats/
│   └── 2022/
├── Attestations/
│   └── 2026/
└── Autres/
    └── 2023/
```

The script automates loading the **entire** list (the "Afficher plus" button)
and then downloads each document into the right folder.

---

## 🪟 Usage on Windows (no Python required)

1. **Download** `mypeopledoc-export.exe` from the latest release of the project.
2. **Double-click** the executable. A Firefox window opens.
3. **Log in** normally to MyPeopleDoc (password + two-factor authentication if requested).
4. **Go to "Mes documents"**.
5. Return to the **black command window** and **press Enter**.
6. Let the script work: it downloads everything automatically.
7. The files are sorted into `Documents\Documents_MyPeopleDoc` by type / year.

> ⚠️ On first launch, Windows SmartScreen may show a warning ("unrecognized
> app") because the executable is **not signed**.
> Click **More info** then **Run anyway**.

---

## 🐧 Usage on Linux

The script needs Python 3.13+ and a terminal.

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies, including Firefox's system libraries
pip install -r requirements.txt
python -m playwright install --with-deps firefox   # may ask for sudo

# 3. Run the export script
python export_mypeopledoc.py
```

Then, in the Firefox window that opens:
1. **Log in** normally to MyPeopleDoc (password + two-factor authentication if requested).
2. **Go to "Mes documents"**.
3. Return to the terminal and **press Enter**.
4. The files are sorted into `Documents/Documents_MyPeopleDoc` by type / year.

---

## 🍎 Usage on macOS

The script needs Python 3.13+ and a terminal.

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
python -m playwright install firefox

# 3. Run the export script
python export_mypeopledoc.py
```

Then, in the Firefox window that opens:
1. **Log in** normally to MyPeopleDoc (password + two-factor authentication if requested).
2. **Go to "Mes documents"**.
3. Return to the terminal and **press Enter**.
4. The files are sorted into `Documents/Documents_MyPeopleDoc` by type / year.

---

## 🐍 Running from source on Windows (advanced)

If you prefer to run from source on Windows instead of using the executable,
with Python 3.13+ installed, from PowerShell or cmd:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install firefox
python export_mypeopledoc.py
```

Available options:

| Option             | Purpose                                   | Default |
|--------------------|-------------------------------------------|---------|
| `--output FOLDER`  | Destination folder                        | `<home>/Documents/Documents_MyPeopleDoc` |
| `--profile-dir`    | Persistent Firefox session folder         | `<home>/.mypeopledoc-playwright-firefox` |

---

## 🔨 Building the Windows executable (PyInstaller)

The executable bundles **Firefox**, so users have nothing to install.

From a Windows machine with Python 3.13:

```bash
git clone <this repository>
cd mypeopledoc
python build_exe.py
```

This produces `dist\mypeopledoc-export.exe`.

> The build must be done **on Windows** to produce a Windows `.exe`.

---

## 🤖 Automatic build (GitHub Actions)

The workflow `.github/workflows/build-exe.yml` automatically builds
`mypeopledoc-export.exe`:

- **On every published release** (the executable is then attached to the release);
- **Manually** from the *Actions* tab → *build-exe* → *Run workflow*.

---

## 🛠️ Troubleshooting

- **A document fails to download**: the script reports it in the final
  summary ("Failures" counter). Run it again; already-present files are
  never overwritten (`_2`, `_3`… are added on duplicates).
- **"No document detected"**: make sure you are on the "Mes documents" page
  before pressing Enter.
- **Downloaded files are empty / weird**: MyPeopleDoc's interface may have
  changed. Open an issue including your browser version and the displayed
  error message.

---

## 📄 Technical notes

The script relies on CSS selectors from the MyPeopleDoc interface
(`article.document-cards`, `a.download`, `span.pin em`, etc.). **These
selectors may change** if MyPeopleDoc updates its application (it is an Ember SPA).

- `PLAYWRIGHT_BROWSERS_PATH=0`: used at build time to bundle Firefox into the executable.
- The executable keeps the Firefox session (`--profile-dir`), so you only
  enter your password once.

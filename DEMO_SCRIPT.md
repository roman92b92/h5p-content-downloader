# Demo / Video Recording Script

This document is a step-by-step walkthrough you can follow while recording a
screen capture or live demo of the H5P Content Downloader.

---

## Before You Record

**Have these ready:**
- [ ] Python 3.8+ installed (`python --version`)
- [ ] A terminal / command prompt open
- [ ] A valid H5P platform account (for the live auth demo)
- [ ] This repository cloned to your machine

**Recommended screen layout:**
- Terminal on the left half
- File Explorer / VS Code on the right half

---

## Scene 1 — Introduction (30 sec)

> "This is the H5P Content Downloader — a Python tool that lets you batch-download
> .h5p files from any H5P.com platform using a simple CSV list."

Show the project folder in Explorer:

```
h5p-content-downloader/
├── h5p_downloader.py
├── convert_csv.py
├── config.example.json
├── requirements.txt
└── examples/
    ├── sample_simple.csv
    └── sample_hierarchical.csv
```

---

## Scene 2 — Installation (1 min)

> "Let's install the two dependencies first."

```bash
# Navigate to the project folder
cd h5p-content-downloader

# Install dependencies (only requests and beautifulsoup4)
pip install -r requirements.txt
```

Expected output:
```
Successfully installed requests-2.31.0 beautifulsoup4-4.12.0 ...
```

> "That's it — just two lightweight libraries."

---

## Scene 3 — Configuration (1 min 30 sec)

> "Now let's set up the config file. We never commit real credentials,
> so we start from the example template."

```bash
# Copy the example config
cp config.example.json config.json
```

Open `config.json` in your editor and walk through each field:

```json
{
  "username":   "your_email@example.com",   ← YOUR LOGIN EMAIL
  "password":   "your_password_here",        ← YOUR PASSWORD
  "base_url":   "https://your-platform.h5p.com",  ← PLATFORM URL
  "csv_file":   "examples/sample_hierarchical.csv", ← CSV TO PROCESS
  "output_dir": "downloads"                  ← WHERE FILES ARE SAVED
}
```

> "The four key variables are:
> 1. **username** — your login email
> 2. **password** — your account password
> 3. **base_url** — the root URL of the H5P platform you're downloading from
> 4. **csv_file** — the path to your CSV list of content URLs"

> "Notice that `config.json` is listed in `.gitignore` — your credentials
> are never tracked by git."

Show `.gitignore`:
```
config.json           ← credentials stay local
session_cookies.pkl   ← session cache stays local
downloads/            ← downloaded files not committed
```

---

## Scene 4 — The CSV Format (2 min)

> "The tool supports two CSV formats. Let's look at the simple one first."

Open `examples/sample_simple.csv`:

```csv
content_name,content_url
Defining Cybersecurity in the Modern World,https://cybint.h5p.com/content/1292545090162314197
The Impact of Cybercrime,https://cybint.h5p.com/content/1292545222332179897
...
```

> "Just two columns: a name and the H5P content URL.
> The URL always contains `/content/` followed by the numeric content ID."

Now show `examples/sample_hierarchical.csv`:

```csv
course,module,section,unit,content_url
Applied Cybersecurity - Foundations,Intro to Cyber,First Steps in Cybersecurity,Information Technology (IT),https://...
Applied Cybersecurity - Foundations,Intro to Cyber,First Steps in Cybersecurity,Information Security,https://...
```

> "The hierarchical format has five columns:
> - **course** → top-level folder
> - **module** → second-level folder
> - **section** → third-level folder
> - **unit** → used as the filename (not a folder)
> - **content_url** → the H5P content page URL"

---

## Scene 5 — Running the Downloader (2 min)

> "Now let's run it."

```bash
python h5p_downloader.py
```

Watch the output — narrate what's happening:

```
============================================================
H5P Content Downloader
Started: 2025-01-15 10:30:00
============================================================

Configuration:
  Platform : https://your-platform.h5p.com
  Username : your_email@example.com
  CSV file : examples/sample_hierarchical.csv
  Output   : downloads/

[INFO] Checking authentication...
[INFO] Session cookies loaded from session_cookies.pkl
[INFO] Testing session validity...
[INFO] Session is valid               ← reuses cached login

[1/15] ────────────────────────────────────
  Course  : Applied Cybersecurity - Foundations
  Module  : Intro to Cyber
  Section : First Steps in Cybersecurity
  Unit    : Information Technology (IT)
  URL     : https://...
[INFO] Analyzing content page...
[INFO] Found exportUrl in H5PIntegration: /media/exports/...
[INFO] DOWNLOADING: information-technology-it-1292541688557791587.h5p
[INFO] Saved 245,760 bytes → downloads/Applied Cybersecurity.../...

...

============================================================
DOWNLOAD SUMMARY
============================================================
  Total      : 15
  Successful : 14
  Failed     : 1
============================================================
```

---

## Scene 6 — Output Folder Structure (1 min)

> "Let's look at what was created."

Show the `downloads/` folder in Explorer:

```
downloads/
└── Applied Cybersecurity - Foundations/
    ├── Kickoff/
    │   └── Program Kickoff/
    │       └── certified-cybersecurity-associate-program-XXXX.h5p
    └── Intro to Cyber/
        ├── First Steps in Cybersecurity/
        │   ├── information-technology-it-XXXX.h5p
        │   └── information-security-XXXX.h5p
        └── Cyberthreats/
            └── common-security-threats-XXXX.h5p
```

> "The folder structure mirrors exactly what was in the CSV —
> Course / Module / Section — and each file is named after the unit."

---

## Scene 7 — Debug Mode (30 sec)

> "If a download fails, the debug flag gives you full visibility."

```bash
python h5p_downloader.py --debug
```

> "This logs every HTTP request, response code, cookie state, and URL pattern
> tried — making it easy to diagnose any issue."

---

## Scene 8 — CSV Converter (1 min 30 sec)

> "If your content list comes from a course planner spreadsheet,
> use the converter first."

```bash
python convert_csv.py "My_Course_Planner_2025.csv"
```

Output:
```
Reading: My_Course_Planner_2025.csv
Total rows: 312

Writing: My_Course_Planner_2025_formatted.csv

============================================================
CONVERSION SUMMARY
============================================================
  Input file    : My_Course_Planner_2025.csv
  Output file   : My_Course_Planner_2025_formatted.csv
  H5P entries   : 187
  ZIP (skipped) : 12
  Other skipped : 113
============================================================
```

> "Then update `csv_file` in config.json to point to the formatted file
> and run the downloader as normal."

---

## Scene 9 — Using a Custom Config (30 sec)

> "You can have multiple config files — one per course — and switch between them."

```bash
# Download one course
python h5p_downloader.py --config foundations.json

# Download another course
python h5p_downloader.py --config advanced_web_pentesting.json
```

---

## Scene 10 — Wrap-Up (30 sec)

> "To summarise:
> 1. Copy `config.example.json` to `config.json` and fill in your credentials
> 2. Prepare a CSV with your content URLs
> 3. Run `python h5p_downloader.py`
>
> The tool handles authentication, session caching, folder creation,
> and downloading — all automatically."

Point to the README for full documentation.

---

## Key Variables Reference

| Variable | File | What to change |
|---|---|---|
| `username` | `config.json` | Your H5P platform login email |
| `password` | `config.json` | Your H5P platform password |
| `base_url` | `config.json` | URL of your H5P platform |
| `csv_file` | `config.json` | Path to your content list CSV |
| `output_dir` | `config.json` | Where to save downloaded files |
| `--config` | Command line | Selects which config file to use |
| `--debug` | Command line | Enables verbose logging |

---

## Common Mistakes to Avoid

- Forgetting to copy `config.example.json` to `config.json` before running
- Leaving placeholder values (`your_email@example.com`) in `config.json`
- Using an SSO/SAML account — those require manual login and are not supported
- Pointing `csv_file` to the wrong path — use relative paths from the project root
- Committing `config.json` to git — the `.gitignore` prevents this by default

---

*End of demo script.*

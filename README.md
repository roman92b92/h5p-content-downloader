# H5P Content Downloader

> Batch-download `.h5p` files from any H5P.com-hosted platform using a simple CSV list.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## Table of Contents

- [What It Does](#what-it-does)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CSV Formats](#csv-formats)
- [Usage](#usage)
- [Output Structure](#output-structure)
- [CSV Converter](#csv-converter)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## What It Does

H5P Content Downloader automates the process of bulk-downloading interactive H5P packages (`.h5p` files) from an H5P.com-hosted learning platform. You provide a CSV file listing the content URLs, and the tool handles:

1. Logging into the platform (with session caching)
2. Navigating to each content page
3. Locating the export/download URL
4. Saving the `.h5p` file to a structured local folder

It is particularly useful for course authors, instructional designers, and LMS administrators who need to archive or migrate H5P content at scale.

---

## Features

| Feature | Description |
|---|---|
| **Session caching** | Stores authentication cookies — no re-login on every run |
| **Two CSV formats** | Supports both a simple list and a hierarchical (course/module/section) format |
| **Auto folder structure** | Creates `Course → Module → Section` folders automatically |
| **Smart URL discovery** | Parses the content page and the H5PIntegration JS config to find the real download URL |
| **Fallback URL patterns** | Tries multiple known H5P export URL patterns if the primary fails |
| **Progress reporting** | Shows per-file status and a final download summary |
| **Debug mode** | `--debug` flag enables verbose logging for troubleshooting |
| **Cross-platform** | Works on Windows, macOS, and Linux |
| **Minimal dependencies** | Only requires `requests` and `beautifulsoup4` |

---

## Prerequisites

- **Python 3.8+** — [Download Python](https://www.python.org/downloads/)
- A valid account on the target H5P.com platform
- The H5P content URLs you want to download (see [CSV Formats](#csv-formats))

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/roman92b92/h5p-content-downloader.git
cd h5p-content-downloader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your config file
cp config.example.json config.json        # macOS / Linux
copy config.example.json config.json      # Windows
# Edit config.json with your credentials (see Configuration section)

# 4. Run with the included example
python h5p_downloader.py
```

> **Note:** `config.json` is listed in `.gitignore` — your credentials will never be committed.

---

## Configuration

Copy `config.example.json` to `config.json` and fill in your values:

```json
{
  "username":   "your_email@example.com",
  "password":   "your_password_here",
  "base_url":   "https://your-platform.h5p.com",
  "csv_file":   "examples/sample_hierarchical.csv",
  "output_dir": "downloads"
}
```

| Key | Required | Description |
|---|---|---|
| `username` | Yes | Email address used to log in to the H5P platform |
| `password` | Yes | Account password |
| `base_url` | Yes | The root URL of your H5P platform (no trailing slash) |
| `csv_file` | Yes | Path to the CSV file containing the content list |
| `output_dir` | No | Folder where downloaded files are saved (default: `downloads`) |

---

## CSV Formats

The downloader supports two CSV formats.

### Format 1 — Simple

Best for a flat list of unrelated content items.

**Columns:** `content_name`, `content_url`

```csv
content_name,content_url
Introduction to Cybersecurity,https://your-platform.h5p.com/content/1292545090162314197
Understanding Cyber Threats,https://your-platform.h5p.com/content/1292545222332179897
Social Engineering Overview,https://your-platform.h5p.com/content/1292542686981355897
```

See [`examples/sample_simple.csv`](examples/sample_simple.csv) for a working example.

---

### Format 2 — Hierarchical (Recommended)

Best for structured courses. Creates a matching folder tree on disk.

**Columns:** `course`, `module`, `section`, `unit`, `content_url`

```csv
course,module,section,unit,content_url
Applied Cybersecurity,Intro to Cyber,First Steps,Information Technology,https://your-platform.h5p.com/content/1292541688557791587
Applied Cybersecurity,Intro to Cyber,First Steps,Information Security,https://your-platform.h5p.com/content/1292541835552265417
Applied Cybersecurity,Intro to Cyber,Cyberthreats,Common Security Threats,https://your-platform.h5p.com/content/1292542662158907687
```

| Column | Folder level | Notes |
|---|---|---|
| `course` | Level 1 folder | Top-level course name |
| `module` | Level 2 folder | Module within the course |
| `section` | Level 3 folder | Section within the module |
| `unit` | Filename base | Used in the `.h5p` filename, **not** a folder |
| `content_url` | — | Full URL to the H5P content page |

See [`examples/sample_hierarchical.csv`](examples/sample_hierarchical.csv) for a working example.

---

## Usage

### Basic run (uses `config.json` by default)

```bash
python h5p_downloader.py
```

### Specify a different config file

```bash
python h5p_downloader.py --config my_course.json
```

### Enable verbose debug logging

```bash
python h5p_downloader.py --config my_course.json --debug
```

### Full help

```bash
python h5p_downloader.py --help
```

---

## Output Structure

For the hierarchical CSV format, files are organised automatically:

```
downloads/
└── Applied Cybersecurity - Foundations/
    ├── Kickoff/
    │   ├── Program Kickoff/
    │   │   └── certified-cybersecurity-associate-program-1292560564737365627.h5p
    │   └── Course Kickoff/
    │       └── foundations-course-1292560564978988367.h5p
    └── Intro to Cyber/
        ├── First Steps in Cybersecurity/
        │   ├── information-technology-it-1292541688557791587.h5p
        │   └── information-security-1292541835552265417.h5p
        └── Cyberthreats/
            └── common-security-threats-1292542662158907687.h5p
```

**Filename pattern:** `<unit-name-slugified>-<content-id>.h5p`

---

## CSV Converter

If your course content lives in a multi-level spreadsheet (e.g. exported from a course planner), use the converter to transform it into the hierarchical format before running the downloader.

### Converter input format

The planner spreadsheet must be exported as CSV with this column layout:

| Column index | Contains |
|---|---|
| 1 | Course name |
| 2 | Module name |
| 3 | Section name |
| 4 | Sub-section (→ becomes the `section` in output) |
| 5 | Unit name |
| 6 | H5P content URL |

The first 3 rows are treated as header/metadata and are skipped automatically.

See [`examples/course_planner_template.csv`](examples/course_planner_template.csv) for the expected layout.

### Run the converter

```bash
python convert_csv.py "My_Course_Planner_2025.csv"
```

This creates `My_Course_Planner_2025_formatted.csv` in the same folder.

Then update your `config.json`:

```json
{
  "csv_file": "My_Course_Planner_2025_formatted.csv"
}
```

---

## Troubleshooting

### Login fails

| Symptom | Likely cause | Fix |
|---|---|---|
| "No password field found" | Wrong email or account not found | Double-check `username` in config.json |
| Redirected to SSO/SAML URL | Account uses SSO | Automated login not supported for SSO accounts |
| "Login Failed" after password | Wrong password | Verify password by logging in manually |
| `ConnectionError` | Platform is unreachable | Check `base_url` in config.json |

### Downloads return HTML instead of `.h5p`

The session may have expired mid-run. Delete `session_cookies.pkl` and run again — it will re-authenticate.

```bash
# Delete stale session
del session_cookies.pkl        # Windows
rm session_cookies.pkl         # macOS / Linux
```

### Files save as 0 bytes

The download URL pattern used by the platform may differ from what the script expects. Run with `--debug` and check the `exportUrl` value found in the logs.

### Windows encoding errors

Make sure you are running Python 3.8+ and that your terminal supports UTF-8. The script automatically reconfigures stdout encoding on Windows.

---

## Project Structure

```
h5p-content-downloader/
├── h5p_downloader.py          # Main downloader — authentication + batch download
├── convert_csv.py             # Converts course planner CSVs to hierarchical format
├── config.example.json        # Config template (copy to config.json and edit)
├── requirements.txt           # Python dependencies
├── .gitignore                 # Excludes credentials and downloads from git
├── LICENSE                    # MIT License
└── examples/
    ├── sample_simple.csv          # Simple format — flat list of content
    ├── sample_hierarchical.csv    # Hierarchical format — course/module/section
    └── course_planner_template.csv # Template for course planner spreadsheet input
```

---

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Commit your changes: `git commit -m "Add my improvement"`
4. Push to the branch: `git push origin feature/my-improvement`
5. Open a Pull Request

Please keep PRs focused and include a clear description of what changed and why.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Disclaimer

> **Use at your own risk.**

This tool is provided as-is, without any warranty of any kind. By using it, you accept full responsibility for any consequences — including but not limited to account suspension, data loss, or legal issues.

- This tool is intended solely for downloading content you have legitimate access to through your own account.
- Always comply with the terms of service of the platform you are downloading from.
- The authors are not responsible for any misuse, damage, or liability arising from the use of this software.

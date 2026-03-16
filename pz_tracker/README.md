# P&Z Meeting Tracker

Automated tool for tracking Planning & Zoning (P&Z) meeting opportunities across multiple Texas cities.

## What It Does

1. Reads city portal URLs from an Excel workbook
2. Scrapes each city portal (JS-heavy sites via Playwright) for the latest P&Z agenda PDF
3. Parses agenda PDFs for relevant items (rezoning, site plans, subdivisions, etc.)
4. Downloads linked detail/staff-report PDFs
5. Uses the Claude API to extract structured applicant data
6. Writes results into city-specific sheets in the Excel workbook
7. Deduplicates entries automatically
8. Optionally runs on a weekly schedule and sends an email summary

## Setup

### 1. Install dependencies

```bash
cd pz_tracker
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

Copy `.env` and fill in your API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

For email summaries (optional):

```
EMAIL_SENDER=you@gmail.com
EMAIL_PASSWORD=app-password
EMAIL_RECIPIENT=boss@company.com
```

### 3. Prepare the Excel file

Place `Cities_P_Z_Meeting_Info.xlsx` in the `pz_tracker/` directory.  
The tool will create city sheets automatically if they don't exist.

## Usage

### Run once (all cities)

```bash
python main.py
```

### Run for a single city

```bash
python main.py --city "Lago Vista"
```

### Run on a weekly schedule

```bash
python main.py --schedule
```

This runs immediately on start, then every Monday at 07:00 (configurable in `config.py`).

## Project Structure

```
pz_tracker/
├── main.py                  # Entry point
├── config.py                # City list, keywords, paths
├── scrapers/
│   ├── base_scraper.py      # Abstract base class
│   ├── civicplus.py         # CivicPlus portals
│   ├── municode.py          # MuniCode Meetings
│   ├── civicclerk.py        # CivicClerk portals
│   ├── civicweb.py          # CivicWeb portals
│   └── standard_html.py     # Generic HTML pages
├── parsers/
│   ├── pdf_parser.py        # PDF text + hyperlink extraction
│   └── ai_extractor.py      # Claude API extraction
├── writers/
│   └── excel_writer.py      # openpyxl writer
├── utils/
│   ├── downloader.py        # PDF download with retry
│   └── deduplicator.py      # Duplicate-entry checker
├── .env                     # API keys (not committed)
├── requirements.txt
└── README.md
```

## Supported Portal Types

| Portal        | Example City | Module             |
| ------------- | ------------ | ------------------ |
| CivicPlus     | Lago Vista   | `civicplus.py`     |
| MuniCode      | Manor        | `municode.py`      |
| CivicClerk    | Sherman      | `civicclerk.py`    |
| CivicWeb      | Victoria     | `civicweb.py`      |
| Standard HTML | Elgin        | `standard_html.py` |

## Adding a New City

1. Add the city to `DEFAULT_CITIES` in `config.py` with its URL and portal type
2. If the portal type is new, create a scraper in `scrapers/` extending `BaseScraper`
3. Register the new scraper class in `SCRAPER_MAP` in `main.py`

## Keywords Tracked

rezoning, preliminary plat, final plat, site plan, planned development, residential, commercial, industrial, restaurant, retail, subdivision, concept plan, zoning change, special use permit

## Excel Output Columns

City | P&Z Date | Applicant Business Name | Applicant Name | Applicant Email | Phone Number | Construction Type | Land Acres | Location | Description | URL | Status

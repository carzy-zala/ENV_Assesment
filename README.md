# Hydrology Data Engineering Pipeline (SQLite, Medallion Architecture, Star Schema)

This project implements a production-style data engineering pipeline that ingests hydrology data from the Environment Agency Hydrology API, stores raw data, transforms it through Medallion layers, and exposes a star-schema model for analytics.

The pipeline demonstrates:

* API ingestion
* Raw data landing
* Structured transformations (Bronze → Silver → Gold)
* Data validation at every layer
* SQLite star schema modeling
* Automated tests
* Config-driven execution

---

## Project Structure

```
.
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── data/
│   └── hydrology.db
├── logs/
│   ├── pipeline.log
│   └── pipeline_error.log
├── utils/
│   ├── connection/
│   ├── errorHandling/
│   └── logging/
├── src/
│   ├── extract/
│   ├── transform/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   └── load/
├── validate/
└── tests/
```

---

## Prerequisites

* Python **3.10+**
* Works on **Windows, macOS, and Linux**
* SQLite (bundled with Python)

---

## Create Virtual Environment

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows (CMD)

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```
---

## Configuration

All runtime configuration lives in `config.py`.

### Example

```python
DB_PATH = "data/hydrology.db"
BASE_URL = "https://environment.data.gov.uk/hydrology"

STATION_REF = "HIPPER_PARK ROAD BRIDGE_E_202312"
LIMIT = 10
PARAMETERS = ["dissolved oxygen", "conductivity"]

APPEND_MODE = False
```

### Config Fields Explained

| Variable    | Meaning                            |
| ----------- | ---------------------------------- |
| DB_PATH     | SQLite file location               |
| BASE_URL    | Hydrology API base endpoint        |
| STATION_REF | Station search string              |
| LIMIT       | Number of latest readings to fetch |
| PARAMETERS  | List of parameters to fetch        |
| APPEND_MODE | Append or overwrite raw datasets   |

---

## Running the Pipeline

From project root:

```bash
python main.py
```

Logs will be written to:

```
logs/pipeline.log
logs/pipeline_error.log
```

---

## Changing the Station

Edit `config.py`:

```python
STATION_REF = "HIPPER_PARK ROAD BRIDGE_E_202312"
```

This value is used to search stations via the Hydrology API.

---

## Changing Parameters

Edit `config.py`:

```python
PARAMETERS = ["temperature", "ph"]
```

The pipeline:

* Confirms the requested parameter exists in station metadata
* Fetches all measures for that parameter
* Fetches all available units (e.g. dissolved oxygen mg/L and %)

### Examples

```python
PARAMETERS = ["turbidity"]
PARAMETERS = ["conductivity", "temperature"]
PARAMETERS = ["dissolved oxygen"]
```

---

## Pipeline Flow

The pipeline uses a **Medallion architecture**:

### 1. DS Layer (Raw Landing)

* Calls Hydrology API
* Stores raw JSON payloads in SQLite
* Each run tagged with `ingested_at`

**Table**

```
raw_landing(id, dataset, payload, ingested_at)
```

---

### 2. DS2B Layer (Raw → Bronze)

Transforms raw JSON into structured tables:

```
bronze_station
bronze_measure
```

Bronze keeps structure with minimal transformation.

---

### 3. B2S Layer (Bronze → Silver)

Silver layer performs:

* Deduplication
* Datetime normalization
* Referential integrity checks

**Tables**

```
silver_station
silver_measure
```

---

### 4. S2G Layer (Silver → Gold)

Gold layer exposes a **star schema**:

```
dim_station
fact_measurement
```

Optimized for querying and analytics.

---

## Validation

Each layer includes validation logic:

| Layer  | Validation                       |
| ------ | -------------------------------- |
| DS     | Raw payload completeness         |
| Bronze | Required fields + schema checks  |
| Silver | Deduplication + integrity checks |
| Gold   | Dimension/fact integrity         |

Failures stop the pipeline immediately.

---

## Database Overview

**Raw**

```
raw_landing
```

**Bronze**

```
bronze_station
bronze_measure
```

**Silver**

```
silver_station
silver_measure
```

**Gold**

```
dim_station
fact_measurement
```

---

## Running Tests

Run all tests:

```bash
pytest -q
```

Tests cover:

* API client mocking
* SQLite schema creation
* DS ingestion logic
* Bronze/Silver/Gold transformations
* Validation logic

---

## Common Issues

### Database schema mismatch

If you see:

```
no column named ingested_at
```

Delete the DB file and rerun:

```bash
rm data/hydrology.db
python main.py
```

---

### No station returned

Try a shorter search term:

```python
STATION_REF = "HIPPER"
```

Or test via browser:

```
https://environment.data.gov.uk/hydrology/id/stations?search=HIPPER
```

---

## Design Notes

* SQLite chosen for portability and interview simplicity
* Medallion architecture demonstrates real-world pipeline layering
* Config-driven design enables easy parameter changes
* Validation ensures data quality at every stage
* Idempotency supported via overwrite/append modes
* Gold star schema suitable for BI tools

---

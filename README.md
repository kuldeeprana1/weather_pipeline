# Weather + Demographics Pipeline

An end-to-end data pipeline that pulls **live weather** for every city in the population
dataset from the [Open-Meteo API](https://open-meteo.com/), merges it with that **static
demographic dataset**, cleans and normalises the result, loads it into **BigQuery**, and
exposes it to a **Looker Studio** dashboard.

```
Open-Meteo API ─┐
                ├─► pandas merge ─► clean / normalise ─► BigQuery ─► SQL view ─► Looker Studio
population.csv ─┘
```

## Project structure

```
weather_pipeline/
├── .gitignore          # keeps data/, .venv/, caches and secrets out of git
├── requirements.txt    # Python dependencies
├── data/
│   └── population.csv  # 28 national capitals + population + coordinates (not committed)
├── scripts/
│   ├── main.py         # the pipeline (extract -> merge -> clean -> load)
│   └── gcp-key.json    # your GCP service account key (NOT committed)
└── sql/
    └── analytics.sql   # Step 5: exploration, aggregation, view
```

## Prerequisites

- Python 3.10+
- A Google Cloud project with BigQuery enabled
- A Google account for Looker Studio
- Git

---

## 1. Local setup

```powershell
cd weather_pipeline
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Get the data

`data/population.csv` must exist with these columns:

```
City,Country,Latitude,Longitude,Population
Tokyo,Japan,35.6895,139.6917,37400068
```

This is the instructor-provided *Global demographic dataset* (sheet `Countries`, 70 rows),
**filtered down to the 28 national capitals it contains** — non-capital cities such as
Shanghai, Mumbai, Istanbul and Toronto are excluded. To convert the `.xlsx`, then keep only
the capital-city rows:

```powershell
.\.venv\Scripts\python.exe -c "import pandas as pd; d=pd.read_excel(r'path\to\Global demographic dataset .xlsx', sheet_name='Countries'); d[['City','Country','Latitude','Longitude','Population']].to_csv('data/population.csv', index=False)"
```

The pipeline processes **every row** in the file, so adding or removing cities needs no code
change. `population.csv` is gitignored, so every clone needs to supply its own copy.

## 3. Run the pipeline locally

Always confirm it works locally **before** touching the cloud:

```powershell
.\.venv\Scripts\python.exe scripts\main.py
```

You should see every capital fetched, a merge summary, and a preview table ending with
`[transform] final shape: (28, 11)`.

## 4. Google Cloud setup

1. Create (or select) a project in the [GCP Console](https://console.cloud.google.com/) and
   note its **Project ID**.
2. Enable the [BigQuery API](https://console.cloud.google.com/apis/library/bigquery.googleapis.com).
3. Create a **Service Account** with the **BigQuery Admin** role.
4. On the account's **Keys** tab, add a new **JSON** key and download it.
5. Save it as `scripts/gcp-key.json`. It is already listed in `.gitignore` — **never commit it.**
6. In BigQuery, create a dataset named `global_weather_data` (multi-region).

If your project ID is different, override it:

```powershell
$env:GCP_PROJECT = "your-real-project-id"
```

## 5. Load into BigQuery

```powershell
.\.venv\Scripts\python.exe scripts\main.py --upload
```

This writes all 28 rows to `<project-id>.global_weather_data.current_weather_stats` using
`WRITE_TRUNCATE` (each run replaces the previous snapshot). The project is taken from the
service-account key unless you override it with `$env:GCP_PROJECT`.

## 6. SQL

Open the BigQuery SQL workspace and run [sql/analytics.sql](sql/analytics.sql) top to bottom:

- **5.1** preview the table and count rows
- **5.2** Top 5 hottest countries with more than 10 million residents
- **5.3** creates the view `vw_hottest_large_countries`

Note: BigQuery does not allow `ORDER BY` / `LIMIT` inside a view definition, so the view
exposes the filtered aggregation and the report applies the ordering.

## 7. Looker Studio dashboard

1. Open [Looker Studio](https://lookerstudio.google.com/) and create a blank report.
2. Add a data source: **BigQuery** connector → project → `global_weather_data` →
   `vw_hottest_large_countries`.
3. Add a **Geo Map**: spatial dimension `Country`, metric `avg_temperature_c`, colour
   gradient blue → red.
4. Add a drop-down control on `TemperatureCategory` (Cold / Mild / Hot).
5. Add a table: `Country | capital_city | TemperatureCategory | avg_temperature_c | population`.
6. Apply a theme, add a title, and click **Share** → *Anyone with the link can view*.

**Gotcha:** a few country names in the source data are not the geo-map canonical form —
notably `UK`, `DR Congo` and `South Korea`. If a country fails to plot, either rename
it in the view (`CASE WHEN Country = 'DR Congo' THEN 'Democratic Republic of the Congo' ...`)
or add `AVG(Latitude)` / `AVG(Longitude)` to the view and plot by coordinates instead.

## 8. Push to GitHub and open a Pull Request

```powershell
git remote add origin https://github.com/<your-username>/weather_pipeline.git
git push -u origin main
git push -u origin feature/data-ingestion
```

Then open a Pull Request on GitHub from `feature/data-ingestion` into `main`.

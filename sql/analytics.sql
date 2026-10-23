-- =============================================================================
-- Step 5 - SQL: querying and transforming the BigQuery table
-- Dataset : formidable-byte-512417-i9.global_weather_data
-- Table   : current_weather_stats
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Step 5.1 - Basic exploration: verify schema definitions and row count
-- -----------------------------------------------------------------------------
SELECT *
FROM `formidable-byte-512417-i9.global_weather_data.current_weather_stats`
LIMIT 10;

-- Row count (expect 28, one row per capital city in population.csv)
SELECT COUNT(*) AS total_rows
FROM `formidable-byte-512417-i9.global_weather_data.current_weather_stats`;


-- -----------------------------------------------------------------------------
-- Step 5.2 - Complex aggregation
-- Goal: identify the Top 5 hottest countries whose capital city has more than
--       10 million residents.
-- -----------------------------------------------------------------------------
SELECT
  Country,
  MAX(City)                        AS capital_city,
  MAX(Population)                  AS population,
  ROUND(AVG(Temperature), 2)       AS avg_temperature_c,
  ROUND(AVG(TemperatureF), 2)      AS avg_temperature_f,
  ROUND(AVG(WindSpeed), 2)         AS avg_wind_speed_kmh
FROM `formidable-byte-512417-i9.global_weather_data.current_weather_stats`
WHERE Population > 10000000
GROUP BY Country
ORDER BY avg_temperature_c DESC
LIMIT 5;


-- -----------------------------------------------------------------------------
-- Step 5.3 - Logical view: reusable semantic layer for the Looker Studio report.
-- NOTE: BigQuery does not allow ORDER BY / LIMIT inside a view definition, so the
--       view exposes the aggregated, filtered rows and the report applies ordering.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `formidable-byte-512417-i9.global_weather_data.vw_hottest_large_countries` AS
SELECT
  Country,
  MAX(City)                         AS capital_city,
  TemperatureCategory,
  MAX(Population)                   AS population,
  ROUND(AVG(Temperature), 2)        AS avg_temperature_c,
  ROUND(AVG(TemperatureF), 2)       AS avg_temperature_f,
  ROUND(AVG(WindSpeed), 2)          AS avg_wind_speed_kmh
FROM `formidable-byte-512417-i9.global_weather_data.current_weather_stats`
WHERE Population > 10000000
GROUP BY Country, TemperatureCategory;

-- Verify the view
SELECT *
FROM `formidable-byte-512417-i9.global_weather_data.vw_hottest_large_countries`
ORDER BY avg_temperature_c DESC
LIMIT 5;

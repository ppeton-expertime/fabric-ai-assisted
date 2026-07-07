# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "5b1b1420-f5cf-4062-8954-4274b98ff92b",
# META       "default_lakehouse_name": "lkh_brz_demo",
# META       "default_lakehouse_workspace_id": "1abc4a08-40a1-42f0-a06a-1fb7f37ceb7f",
# META       "known_lakehouses": [
# META         {
# META           "id": "ecf60434-27a9-47c1-8ae7-520c8c71c071"
# META         },
# META         {
# META           "id": "83123dcb-94a4-42d8-b5f6-6242bf2c46dc"
# META         },
# META         {
# META           "id": "5b1b1420-f5cf-4062-8954-4274b98ff92b"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Pipeline Medallion CITY (Bronze -> Silver -> Gold)
# 
# Ce notebook charge le CSV en Bronze (PySpark), puis construit Silver et Gold en Spark SQL avec nommage 4 parties `workspace.lakehouse.schema.table`.

# CELL ********************

# Bronze: creation du schema CITY dans le Lakehouse par defaut (lkh_brz_demo)
spark.sql("CREATE SCHEMA IF NOT EXISTS CITY")

# Lecture du CSV bronze (header=true, inferSchema=true)
df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv("Files/CITY/city_safety_seattle.csv")
)

# Conserver strictement les 11 colonnes de l'entete
if len(df.columns) != 11:
    raise ValueError(f"Le CSV attendu doit contenir 11 colonnes, trouve: {len(df.columns)}")

df = df.select(*df.columns)

# Test: verifier que le DataFrame n'est pas vide
row_count = df.count()
if row_count == 0:
    raise ValueError("Le DataFrame df est vide (0 ligne).")

# Ecriture idempotente en Bronze
(
    df.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("CITY.city_safety")
)

print(f"Bronze CITY.city_safety row count: {row_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC CREATE SCHEMA IF NOT EXISTS ws_assisted_dev.lkh_slv_demo.CITY;
# MAGIC 
# MAGIC CREATE OR REPLACE TABLE ws_assisted_dev.lkh_slv_demo.CITY.city_safety AS
# MAGIC SELECT
# MAGIC   dataSubtype,
# MAGIC   category,
# MAGIC   NULLIF(TRIM(subcategory), 'NULL') AS subcategory,
# MAGIC   NULLIF(TRIM(status), 'NULL') AS status,
# MAGIC   NULLIF(TRIM(source), 'NULL') AS source,
# MAGIC   to_timestamp(dateTime, 'yyyy-MM-dd HH:mm:ss') AS event_datetime,
# MAGIC   CAST(latitude AS double) AS latitude,
# MAGIC   CAST(longitude AS double) AS longitude,
# MAGIC   year(to_timestamp(dateTime, 'yyyy-MM-dd HH:mm:ss')) AS event_year,
# MAGIC   month(to_timestamp(dateTime, 'yyyy-MM-dd HH:mm:ss')) AS event_month,
# MAGIC   current_timestamp() AS Sid_LoadTimestamp,
# MAGIC   'city_safety_seattle.csv' AS Sid_SourceFile
# MAGIC FROM CITY.city_safety;
# MAGIC 
# MAGIC SELECT COUNT(*) AS silver_row_count
# MAGIC FROM ws_assisted_dev.lkh_slv_demo.CITY.city_safety;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC CREATE SCHEMA IF NOT EXISTS ws_assisted_dev.lkh_gld_demo.CITY;
# MAGIC 
# MAGIC CREATE OR REPLACE TABLE ws_assisted_dev.lkh_gld_demo.CITY.city_safety_by_category AS
# MAGIC SELECT
# MAGIC   dataSubtype,
# MAGIC   category,
# MAGIC   event_year,
# MAGIC   event_month,
# MAGIC   COUNT(*) AS nb_incidents
# MAGIC FROM ws_assisted_dev.lkh_slv_demo.CITY.city_safety
# MAGIC GROUP BY
# MAGIC   dataSubtype,
# MAGIC   category,
# MAGIC   event_year,
# MAGIC   event_month;
# MAGIC 
# MAGIC SELECT COUNT(*) AS gold_row_count
# MAGIC FROM ws_assisted_dev.lkh_gld_demo.CITY.city_safety_by_category;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

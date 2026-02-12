import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, DB_URL


# -----------------------------
# Параметры подключения к БД
CSV_PATH = "final.csv"
df = pd.read_csv(CSV_PATH)


# -----------------------------
# Приведение названий колонок

df = df.rename(columns={
    "TERRITORY_CODE": "territory_code",
    "TERRITORY_NAME": "territory_name",
    "DATE_OF_ARRIVAL": "arrival_date",
    "TRIP_TYPE": "trip_type",
    "VISIT_TYPE": "visit_type",
    "HOME_COUNTRY": "home_country",
    "HOME_REGION": "home_region",
    "HOME_CITY": "home_city",
    "GOAL": "goal",
    "GENDER": "gender",
    "AGE": "age_group",
    "INCOME": "income_group",
    "DAYS_CNT": "days_cnt",
    "VISITORS_CNT": "visitors_cnt",
    "SPENT": "spent_mln"
})


# -----------------------------
# Приведение типов

df["arrival_date"] = pd.to_datetime(
    df["arrival_date"], errors="coerce"
).dt.date

# числовые поля
df["days_cnt"] = pd.to_numeric(df["days_cnt"], errors="coerce").astype("Int64")
df["visitors_cnt"] = pd.to_numeric(df["visitors_cnt"], errors="coerce").astype("Int64")
df["spent_mln"] = pd.to_numeric(df["spent_mln"], errors="coerce").astype("float64")


df["spent_mln"] = df["spent_mln"].fillna(0) 
df["spent_mln"] = df["spent_mln"].astype("float64")

# пустые строки -> NULL, удаление критических пропусков

df = df.dropna(subset=["days_cnt", "visitors_cnt", "arrival_date"])
df = df.where(pd.notnull(df), None) #в df только None, потом в sql вставится NULL

# -----------------------------
# Загрузка данных в таблицу

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = conn.cursor()

insert_query = """
    INSERT INTO tourism_facts (
        territory_code, territory_name, arrival_date, trip_type, visit_type,
        home_country, home_region, home_city, goal, gender, age_group,
        income_group, days_cnt, visitors_cnt, spent_mln
    ) VALUES %s
"""

# Преобразуем DataFrame в список кортежей
data_tuples = [tuple(row) for row in df.values]

# Вставка одним вызовом (с автоматическим батчингом)
execute_values(cursor, insert_query, data_tuples)

conn.commit()
cursor.close()

# -----------------------------
# Проверка загрузки

cursor = conn.cursor()
check_query = """
SELECT
    COUNT(*) AS rows_cnt,
    SUM(visitors_cnt) AS total_visitors,
    MIN(arrival_date) AS min_date,
    MAX(arrival_date) AS max_date
FROM tourism_facts;
"""

cursor.execute(check_query)
result = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
check_df = pd.DataFrame(result, columns=columns)
print(check_df)

cursor.close()
conn.close()



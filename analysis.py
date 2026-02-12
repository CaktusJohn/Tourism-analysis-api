import json
import psycopg2
import pandas as pd
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

def fetch_dataframe(query, params=None):

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    df = pd.read_sql(query, conn, params=params)  # выполняет запрос и возвращает df
    conn.close()
    return df
  

#  Расчёт показателей
def calculate_kpi(start_date=None, end_date=None):

    result = {}  # словарь

    # формирование фильтра по диапазону дат
    where_clause = ""
    params = None

    if start_date and end_date:
        where_clause = "WHERE arrival_date BETWEEN %(start)s AND %(end)s"
        params = {"start": start_date, "end": end_date}

    # 1. Общее количество туристов
    query_total = f"""
        SELECT SUM(visitors_cnt) AS total_visitors
        FROM tourism_facts
        {where_clause};
    """
    total_df = fetch_dataframe(query_total, params)
    result["total_visitors"] = int(total_df["total_visitors"][0] or 0)

    # 2. Туристы по месяцам (date trunk('month')) усекает до месяца
    query_monthly = f"""
        SELECT
            TO_CHAR(DATE_TRUNC('month', arrival_date), 'YYYY-MM-DD') AS month,
            SUM(visitors_cnt) AS visitors
        FROM tourism_facts
        {where_clause}
        GROUP BY month
        ORDER BY month;
    """
    monthly_df = fetch_dataframe(query_monthly, params)
    result["monthly_visitors"] = (
        monthly_df.assign(month=monthly_df["month"].astype(str))
        .to_dict(orient="records")
    )

    # 3. Территориальное распределение
    query_geo = f"""
        SELECT
            home_country,
            SUM(visitors_cnt) AS visitors
        FROM tourism_facts
        {where_clause}
        GROUP BY home_country
        ORDER BY visitors DESC;
    """
    geo_df = fetch_dataframe(query_geo, params)
    result["territorial_distribution"] = geo_df.to_dict(orient="records")

    # 4. Демографическое распределение
    query_demo = f"""
        SELECT
            gender,
            age_group,
            SUM(visitors_cnt) AS visitors
        FROM tourism_facts
        {where_clause}
        GROUP BY gender, age_group
        ORDER BY visitors DESC;
    """
    demo_df = fetch_dataframe(query_demo, params)
    result["demographic_distribution"] = demo_df.to_dict(orient="records")

    # 5. Самая выгодная категория туристов
        # Топ по выручке
    query_by_revenue = f"""
        SELECT
            goal,
            SUM(visitors_cnt) AS visitors,
            SUM(spent_mln) AS revenue,
            SUM(spent_mln) / NULLIF(SUM(visitors_cnt),0) AS avg_spent_per_person
        FROM tourism_facts
        {where_clause}
        GROUP BY goal
        ORDER BY revenue DESC
        LIMIT 1;
    """
    # Топ по количеству туристов
    query_by_visitors = f"""
        SELECT
            goal,
            SUM(visitors_cnt) AS visitors,
            SUM(spent_mln) AS revenue,
            SUM(spent_mln) / NULLIF(SUM(visitors_cnt),0) AS avg_spent_per_person
        FROM tourism_facts
        {where_clause}
        GROUP BY goal
        ORDER BY visitors DESC
        LIMIT 1;
    """

    result["most_profitable_category"] = fetch_dataframe(
        query_by_revenue, params
    ).iloc[0].to_dict()

    result["most_popular_category"] = fetch_dataframe(
        query_by_visitors, params
    ).iloc[0].to_dict()


    # 6. Профиль среднестатистического туриста
    query_profile = f"""
        WITH gender_stat AS (
            SELECT gender, SUM(visitors_cnt) AS visitors
            FROM tourism_facts
            {where_clause}
            GROUP BY gender
            ORDER BY visitors DESC
            LIMIT 1
        ),
        age_stat AS (
            SELECT age_group, SUM(visitors_cnt) AS visitors
            FROM tourism_facts
            {where_clause}
            GROUP BY age_group
            ORDER BY visitors DESC
            LIMIT 1
        ),
        income_stat AS (
            SELECT income_group, SUM(visitors_cnt) AS visitors
            FROM tourism_facts
            {where_clause}
            GROUP BY income_group
            ORDER BY visitors DESC
            LIMIT 1
        ),
        goal_stat AS (
            SELECT goal, SUM(visitors_cnt) AS visitors
            FROM tourism_facts
            {where_clause}
            GROUP BY goal
            ORDER BY visitors DESC
            LIMIT 1
        )
        SELECT
            (SELECT gender FROM gender_stat) AS top_gender,
            (SELECT age_group FROM age_stat) AS top_age_group,
            (SELECT income_group FROM income_stat) AS top_income_group,
            (SELECT goal FROM goal_stat) AS top_goal;
    """

    profile_df = fetch_dataframe(query_profile, params)
    result["average_tourist_profile"] = profile_df.iloc[0].to_dict()


    return result



# Сохранение в JSON
if __name__ == "__main__":

    #kpi_data = calculate_kpi("2021-01-01", "2021-04-02")

    kpi_data = calculate_kpi()

    with open("kpi.json", "w", encoding="utf-8") as f:
        json.dump(kpi_data, f, ensure_ascii=False, indent=4)

    print("Аналитика успешно рассчитана и сохранена в kpi.json")

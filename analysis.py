import json
import psycopg2
import pandas as pd
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME



def fetch_dataframe(query):

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    df = pd.read_sql(query, conn) #выполняет запрос и возвращает df
    conn.close()
    return df
  

#  Расчёт показателей
def calculate_kpi():

    result = {} #словарь

    # 1. Общее количество туристов
    query_total = """
        SELECT SUM(visitors_cnt) AS total_visitors
        FROM tourism_facts;
    """
    total_df = fetch_dataframe(query_total)
    result["total_visitors"] = int(total_df["total_visitors"][0])

    # 2. Туристы по месяцам (date trunk('month')) усекает до месяца
    query_monthly = """
        SELECT
            TO_CHAR(DATE_TRUNC('month', arrival_date), 'YYYY-MM-DD') AS month,
            SUM(visitors_cnt) AS visitors
        FROM tourism_facts
        GROUP BY month
        ORDER BY month;
    """
    monthly_df = fetch_dataframe(query_monthly)
    result["monthly_visitors"] = (
        monthly_df.assign(month=monthly_df["month"].astype(str))
        .to_dict(orient="records")
    )

    # 3. Территориальное распределение
    query_geo = """
        SELECT
            home_country,
            SUM(visitors_cnt) AS visitors
        FROM tourism_facts
        GROUP BY home_country
        ORDER BY visitors DESC;
    """
    geo_df = fetch_dataframe(query_geo)
    result["territorial_distribution"] = geo_df.to_dict(orient="records")

    # 4. Демографическое распределение
    query_demo = """
        SELECT
            gender,
            age_group,
            SUM(visitors_cnt) AS visitors
        FROM tourism_facts
        GROUP BY gender, age_group
        ORDER BY visitors DESC;
    """
    demo_df = fetch_dataframe(query_demo)
    result["demographic_distribution"] = demo_df.to_dict(orient="records")

    # 5. Самая выгодная категория туристов
        # Топ по выручке
    query_by_revenue = """
        SELECT
            goal,
            SUM(visitors_cnt) AS visitors,
            SUM(spent_mln) AS revenue,
            SUM(spent_mln) / NULLIF(SUM(visitors_cnt),0) AS avg_spent_per_person
        FROM tourism_facts
        GROUP BY goal
        ORDER BY revenue DESC
        LIMIT 1;
    """
    # Топ по количеству туристов
    query_by_visitors = """
        SELECT
            goal,
            SUM(visitors_cnt) AS visitors,
            SUM(spent_mln) AS revenue,
            SUM(spent_mln) / NULLIF(SUM(visitors_cnt),0) AS avg_spent_per_person
        FROM tourism_facts
        GROUP BY goal
        ORDER BY visitors DESC
        LIMIT 1;
    """

    result["most_profitable_category"] = fetch_dataframe(query_by_revenue).iloc[0].to_dict()
    result["most_popular_category"] = fetch_dataframe(query_by_visitors).iloc[0].to_dict()


    # 6. Профиль среднестатистического туриста
    query_profile = """
        SELECT
            MODE() WITHIN GROUP (ORDER BY gender) AS top_gender,
            MODE() WITHIN GROUP (ORDER BY age_group) AS top_age_group,
            MODE() WITHIN GROUP (ORDER BY income_group) AS top_income_group,
            MODE() WITHIN GROUP (ORDER BY goal) AS top_goal
        FROM tourism_facts;
    """
    profile_df = fetch_dataframe(query_profile)
    result["average_tourist_profile"] = profile_df.iloc[0].to_dict()

    return result



# Сохранение в JSON
if __name__ == "__main__":

    kpi_data = calculate_kpi()

    with open("kpi.json", "w", encoding="utf-8") as f:
        json.dump(kpi_data, f, ensure_ascii=False, indent=4)

    print("Аналитика успешно рассчитана и сохранена в kpi.json")

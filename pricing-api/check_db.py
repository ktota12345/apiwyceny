import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)

cur = conn.cursor()

# TimoCom 34->79 (DE49->PL20)
cur.execute("SELECT COUNT(*) FROM public.offers WHERE starting_id=34 AND destination_id=79")
print(f"TimoCom 34->79 (DE49->PL20): {cur.fetchone()[0]} rekordów")

# TimoCom 79->34 (PL20->DE49 - odwrotny kierunek)
cur.execute("SELECT COUNT(*) FROM public.offers WHERE starting_id=79 AND destination_id=34")
print(f"TimoCom 79->34 (PL20->DE49): {cur.fetchone()[0]} rekordów")

# Trans.eu 98->135 (DE49->PL20)
cur.execute('SELECT COUNT(*) FROM public."OffersTransEU" WHERE starting_id=98 AND destination_id=135')
print(f"Trans.eu 98->135 (DE49->PL20): {cur.fetchone()[0]} rekordów")

# Trans.eu 135->98 (PL20->DE49 - odwrotny kierunek)
cur.execute('SELECT COUNT(*) FROM public."OffersTransEU" WHERE starting_id=135 AND destination_id=98')
print(f"Trans.eu 135->98 (PL20->DE49): {cur.fetchone()[0]} rekordów")

print("\n" + "="*60)

# Sprawdź przykładowe dane dla TimoCom 34->79
cur.execute("""
    SELECT 
        starting_id, destination_id, enlistment_date,
        ROUND(AVG(trailer_avg_price_per_km), 4) as avg_price
    FROM public.offers 
    WHERE starting_id=34 AND destination_id=79
    GROUP BY starting_id, destination_id, enlistment_date
    ORDER BY enlistment_date DESC
    LIMIT 3
""")
print("\nTimoCom 34->79 przykładowe dane:")
for row in cur.fetchall():
    print(f"  {row}")

# Sprawdź przykładowe dane dla Trans.eu 98->135
cur.execute("""
    SELECT 
        starting_id, destination_id, enlistment_date,
        ROUND(AVG(lorry_avg_price_per_km), 4) as avg_price
    FROM public."OffersTransEU"
    WHERE starting_id=98 AND destination_id=135
    GROUP BY starting_id, destination_id, enlistment_date
    ORDER BY enlistment_date DESC
    LIMIT 3
""")
print("\nTrans.eu 98->135 przykładowe dane:")
for row in cur.fetchall():
    print(f"  {row}")

conn.close()

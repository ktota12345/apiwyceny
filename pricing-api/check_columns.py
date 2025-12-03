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

# Kolumny tabeli offers (TimoCom)
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='public' AND table_name='offers' 
    ORDER BY ordinal_position
""")
print("Tabela public.offers (TimoCom):")
print("="*60)
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print()

# Kolumny tabeli OffersTransEU (Trans.eu)
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='public' AND table_name='OffersTransEU' 
    ORDER BY ordinal_position
""")
print("Tabela public.OffersTransEU (Trans.eu):")
print("="*60)
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()

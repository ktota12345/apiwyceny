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

# Kolumny median w tabeli offers
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema='public' AND table_name='offers' 
    AND column_name LIKE '%median%'
    ORDER BY column_name
""")

print("Kolumny median w tabeli offers:")
for row in cur.fetchall():
    print(f"  {row[0]}")

conn.close()

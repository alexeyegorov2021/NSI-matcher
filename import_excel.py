import pandas as pd
from sqlalchemy import create_engine

# Вставь сюда свою строку подключения из Neon
DATABASE_URL = "postgresql://neondb_owner:npg_4oO8ChdXTVJY@ep-delicate-truth-atrxd47r-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Читаем Excel
df = pd.read_excel("НСИ.xlsx", sheet_name="Лист1", header=None)
df.columns = ["название", "единица_измерения", "код"]

# Убираем пустые строки
df = df.dropna(how="all")

print(f"Загружено строк: {len(df)}")
print(df.head())

# Загружаем в базу данных
engine = create_engine(DATABASE_URL)
df.to_sql("номенклатура", engine, if_exists="replace", index=False)

print("✅ Данные успешно загружены в базу!")

import pandas as pd
from rapidfuzz import process, fuzz
from sqlalchemy import create_engine

# Вставь сюда свою строку подключения из Neon
DATABASE_URL = "postgresql://neondb_owner:npg_4oO8ChdXTVJY@ep-delicate-truth-atrxd47r-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Загружаем базу НСИ из Neon
engine = create_engine(DATABASE_URL)
nsi = pd.read_sql("SELECT название, код, единица_измерения FROM номенклатура", engine)

# Загружаем файл с наименованиями для подбора
input_df = pd.read_excel("Подбор.xlsx", sheet_name="Лист1", header=None)
input_df.columns = ["наименование"]
input_df = input_df.dropna()

# Список наименований из НСИ для сравнения
nsi_names = nsi["название"].tolist()

results = []

for name in input_df["наименование"]:
    match = process.extractOne(
        str(name),
        nsi_names,
        scorer=fuzz.token_sort_ratio
    )

    if match:
        matched_name, score, idx = match
        matched_row = nsi.iloc[idx]
        results.append({
            "исходное_наименование": name,
            "найденное_наименование": matched_name,
            "код": matched_row["код"],
            "единица_измерения": matched_row["единица_измерения"],
            "уверенность_%": score
        })
    else:
        results.append({
            "исходное_наименование": name,
            "найденное_наименование": "",
            "код": "",
            "единица_измерения": "",
            "уверенность_%": 0
        })

result_df = pd.DataFrame(results)
result_df = result_df.sort_values("уверенность_%")
result_df.to_excel("результат_подбора.xlsx", index=False)

print(f"✅ Готово! Обработано {len(result_df)} позиций.")
print(f"   Высокая уверенность (>80%): {len(result_df[result_df['уверенность_%'] > 80])}")
print(f"   Требуют проверки (<80%):    {len(result_df[result_df['уверенность_%'] <= 80])}")
print("   Результат сохранён в: результат_подбора.xlsx")
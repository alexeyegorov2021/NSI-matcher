import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Вставь сюда свою строку подключения из Neon
DATABASE_URL = "postgresql://neondb_owner:npg_4oO8ChdXTVJY@ep-delicate-truth-atrxd47r-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require"

st.set_page_config(page_title="НСИ — Справочник номенклатуры", layout="wide")
st.title("📦 Справочник номенклатуры (НСИ)")

engine = create_engine(DATABASE_URL)

# Загружаем данные
@st.cache_data
def load_data():
    return pd.read_sql("SELECT * FROM номенклатура", engine)

df = load_data()

# Поиск
search = st.text_input("🔍 Поиск по названию или коду")

if search:
    mask = (
        df["название"].str.contains(search, case=False, na=False) |
        df["код"].str.contains(search, case=False, na=False)
    )
    df = df[mask]

# Фильтр по единице измерения
units = ["Все"] + sorted(df["единица_измерения"].dropna().unique().tolist())
selected_unit = st.selectbox("Единица измерения", units)

if selected_unit != "Все":
    df = df[df["единица_измерения"] == selected_unit]

# Показываем таблицу
st.write(f"Найдено позиций: **{len(df)}**")
st.dataframe(df, use_container_width=True, hide_index=True)

# Экспорт в Excel
excel_data = df.to_excel("export.xlsx", index=False)
with open("export.xlsx", "rb") as f:
    st.download_button(
        label="⬇️ Скачать в Excel",
        data=f,
        file_name="номенклатура_экспорт.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

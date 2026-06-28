import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from rapidfuzz import process, fuzz
import io

DATABASE_URL = "postgresql://neondb_owner:npg_4oO8ChdXTVJY@ep-delicate-truth-atrxd47r-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require"

st.set_page_config(page_title="НСИ — Справочник номенклатуры", layout="wide")
st.title("📦 Справочник номенклатуры (НСИ)")

engine = create_engine(DATABASE_URL)

@st.cache_data
def load_data():
    return pd.read_sql("SELECT * FROM номенклатура", engine)

nsi_df = load_data()

tab1, tab2 = st.tabs(["📋 Справочник НСИ", "🔍 Ручное уточнение"])

# ─── Вкладка 1: Справочник ────────────────────────────────────────────────────
with tab1:
    df = nsi_df.copy()

    search = st.text_input("🔍 Поиск по названию или коду")
    if search:
        mask = (
            df["название"].str.contains(search, case=False, na=False) |
            df["код"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    units = ["Все"] + sorted(df["единица_измерения"].dropna().unique().tolist())
    selected_unit = st.selectbox("Единица измерения", units)
    if selected_unit != "Все":
        df = df[df["единица_измерения"] == selected_unit]

    st.write(f"Найдено позиций: **{len(df)}**")
    st.dataframe(df, use_container_width=True, hide_index=True)

    output = io.BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label="⬇️ Скачать в Excel",
        data=output.getvalue(),
        file_name="номенклатура_экспорт.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ─── Вкладка 2: Ручное уточнение ──────────────────────────────────────────────
with tab2:
    st.subheader("Загрузи файл с наименованиями для подбора")
    uploaded_file = st.file_uploader("Выбери Excel-файл (.xlsx)", type=["xlsx"])

    if uploaded_file:
        input_df = pd.read_excel(uploaded_file, header=None)
        input_df.columns = ["наименование"] + [f"col_{i}" for i in range(1, len(input_df.columns))]
        input_df = input_df[["наименование"]].dropna().reset_index(drop=True)

        nsi_names = nsi_df["название"].tolist()

        @st.cache_data
        def match_all(names_tuple, nsi_names_tuple):
            results = []
            for name in names_tuple:
                matches = process.extract(
                    str(name), list(nsi_names_tuple),
                    scorer=fuzz.token_sort_ratio,
                    limit=20
                )
                results.append(matches)
            return results

        with st.spinner("Выполняю подбор..."):
            all_matches = match_all(
                tuple(input_df["наименование"].tolist()),
                tuple(nsi_names)
            )

        st.success(f"Готово! Загружено позиций: **{len(input_df)}**")
        st.info("Для каждой позиции выбран лучший вариант. При необходимости измени вручную и скачай результат.")
        st.markdown("---")

        # Инициализируем выборы в session_state
        key = str(uploaded_file.name)
        if f"selections_{key}" not in st.session_state:
            st.session_state[f"selections_{key}"] = {i: 0 for i in range(len(input_df))}

        selections = st.session_state[f"selections_{key}"]

        # Показываем каждую строку
        for i, row in input_df.iterrows():
            name = row["наименование"]
            matches = all_matches[i]
            # Топ-20 только для этой строки
            options = [f"{m[0]}  ({m[1]}%)" for m in matches]

            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"**{name}**")
            with col2:
                chosen = st.selectbox(
                    label="",
                    options=options,
                    index=selections.get(i, 0),
                    key=f"sel_{key}_{i}",
                    label_visibility="collapsed",
                    on_change=lambda idx=i, opts=options: selections.update(
                        {idx: opts.index(st.session_state.get(f"sel_{key}_{idx}", opts[0]))}
                    )
                )

        st.markdown("---")

        # Собираем финальный результат
        result_rows = []
        for i, row in input_df.iterrows():
            name = row["наименование"]
            matches = all_matches[i]
            options = [f"{m[0]}  ({m[1]}%)" for m in matches]
            sel_idx = selections.get(i, 0)
            matched_name, score, _ = matches[sel_idx]
            matched_row = nsi_df[nsi_df["название"] == matched_name]
            kod = matched_row.iloc[0]["код"] if not matched_row.empty else ""
            ed = matched_row.iloc[0]["единица_измерения"] if not matched_row.empty else ""
            result_rows.append({
                "исходное_наименование": name,
                "выбранное_наименование": matched_name,
                "код": kod,
                "единица_измерения": ed,
                "уверенность_%": score
            })

        result_df = pd.DataFrame(result_rows)
        output = io.BytesIO()
        result_df.to_excel(output, index=False)

        st.download_button(
            label="⬇️ Скачать результат в Excel",
            data=output.getvalue(),
            file_name="результат_уточнения.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
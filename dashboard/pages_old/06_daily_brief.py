"""Daily brief viewer with language toggle."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.aggregator import get_available_dates
from src.config import get_db_path
from src.db import create_tables, get_connection, get_daily_brief

st.set_page_config(page_title="Daily Brief", layout="wide")
st.title("Resumo Diario / Daily Brief")

db_path = get_db_path()
if not db_path.exists():
    st.warning("Database nao encontrada.")
    st.stop()

conn = get_connection(db_path)
create_tables(conn)

dates = get_available_dates(conn)
if not dates:
    st.info("Nenhum dado coletado ainda.")
    conn.close()
    st.stop()

# Controls
col1, col2 = st.columns([2, 1])
with col1:
    selected_date = st.selectbox("Data", dates, index=len(dates) - 1)
with col2:
    language = st.radio("Idioma", ["EN", "PT-BR"], horizontal=True)

lang_code = "pt" if language == "PT-BR" else "en"

brief = get_daily_brief(conn, selected_date, lang_code)

if brief:
    st.markdown(brief)
else:
    st.info(
        f"Nenhum brief gerado para {selected_date} ({language}). "
        f"Execute: `python scripts/generate_brief.py --date {selected_date}`"
    )

# Regenerate button
if st.button("Regenerar Brief"):
    with st.spinner("Gerando brief via Claude API..."):
        try:
            from src.summarizer import generate_brief as gen_brief
            new_brief = gen_brief(conn, selected_date, lang_code)
            st.success("Brief regenerado!")
            st.markdown(new_brief)
        except Exception as e:
            st.error(f"Erro ao gerar brief: {e}")

conn.close()

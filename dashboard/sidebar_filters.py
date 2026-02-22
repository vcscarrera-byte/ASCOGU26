"""Shared sidebar filters for all dashboard pages."""

import sqlite3

import streamlit as st

from src.aggregator import get_available_dates
from src.clinical_filters import get_drug_names, get_tumor_type_names


def render_sidebar_filters(
    conn: sqlite3.Connection,
    show_date: bool = True,
    show_curated: bool = True,
    show_limit: bool = True,
    show_search: bool = False,
    show_sort: bool = False,
    default_limit: int = 20,
    max_limit: int = 50,
) -> dict:
    """Render shared sidebar filters and return current selections.

    Returns dict with keys:
        date_filter: str | None
        curated_only: bool
        selected_tumors: list[str]
        selected_drugs: list[str]
        limit: int
        text_search: str
        sort_by: str
    """
    result = {
        "date_filter": None,
        "curated_only": False,
        "selected_tumors": [],
        "selected_drugs": [],
        "limit": default_limit,
        "text_search": "",
        "sort_by": "relevance",
    }

    # Date filter
    if show_date:
        dates = get_available_dates(conn)
        if dates:
            date_options = ["Todos os dias"] + dates
            selected = st.sidebar.selectbox("Data", date_options)
            result["date_filter"] = None if selected == "Todos os dias" else selected

    # Search
    if show_search:
        result["text_search"] = st.sidebar.text_input(
            "Buscar no texto",
            placeholder="ex: enzalutamide, mCRPC...",
        )

    # Sort
    if show_sort:
        sort_options = {
            "relevance": "Relevancia",
            "engagement": "Engagement",
            "recent": "Mais recentes",
        }
        result["sort_by"] = st.sidebar.selectbox(
            "Ordenar por",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
        )

    # Curated only
    if show_curated:
        result["curated_only"] = st.sidebar.checkbox("Apenas KOLs curados", value=False)

    # Clinical filters section
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filtros Clinicos**")

    # Tumor type multiselect
    tumor_options = get_tumor_type_names()
    if tumor_options:
        result["selected_tumors"] = st.sidebar.multiselect(
            "Tipo de Tumor",
            options=tumor_options,
            default=[],
            help="Deixe vazio para mostrar todos",
        )

    # Drug multiselect
    drug_options = get_drug_names()
    if drug_options:
        result["selected_drugs"] = st.sidebar.multiselect(
            "Medicacao",
            options=drug_options,
            default=[],
            help="Deixe vazio para mostrar todos",
        )

    # Limit slider
    if show_limit:
        result["limit"] = st.sidebar.slider("Limite", 5, max_limit, default_limit)

    # Clear filters button
    has_active = result["selected_tumors"] or result["selected_drugs"] or result["text_search"]
    if has_active:
        if st.sidebar.button("Limpar filtros"):
            st.session_state.clear()
            st.rerun()

    # Show active filter indicator
    active_filters = []
    if result["selected_tumors"]:
        active_filters.append(f"Tumor: {', '.join(result['selected_tumors'])}")
    if result["selected_drugs"]:
        active_filters.append(f"Droga: {', '.join(result['selected_drugs'])}")
    if result["text_search"]:
        active_filters.append(f"Busca: \"{result['text_search']}\"")
    if active_filters:
        st.sidebar.markdown("---")
        st.sidebar.caption("Filtros ativos: " + " | ".join(active_filters))

    return result

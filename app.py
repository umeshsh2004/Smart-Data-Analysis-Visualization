from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.new_project.preprocessing import apply_preprocessing
from src.new_project.filters import apply_filters, build_filter_spec


@dataclass
class LoadedData:
    df: pd.DataFrame
    name: str


def _upload_key(name: str, raw: bytes) -> tuple[str, int, int]:
    return (name, len(raw), hash(raw))


def _read_upload(name: str, raw: bytes) -> LoadedData:
    bio = io.BytesIO(raw)
    filename = name

    lower = filename.lower()
    if lower.endswith(".csv"):
        df = pd.read_csv(bio)
    elif lower.endswith(".xlsx") or lower.endswith(".xls"):
        df = pd.read_excel(bio)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

    return LoadedData(df=df, name=filename)


def _numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    num = df.select_dtypes(include=[np.number])
    if num.shape[1] == 0:
        return pd.DataFrame()
    out = pd.DataFrame(
        {
            "count": num.count(),
            "mean": num.mean(numeric_only=True),
            "median": num.median(numeric_only=True),
            "std": num.std(numeric_only=True),
            "min": num.min(numeric_only=True),
            "max": num.max(numeric_only=True),
        }
    )
    return out


def _viz_panel(df: pd.DataFrame) -> None:
    st.subheader("Visualization")

    if df.empty:
        st.info("No rows to visualize (filters may have removed all rows).")
        return

    chart = st.selectbox(
        "Chart type",
        ["Bar", "Line", "Pie", "Histogram", "Scatter"],
        index=0,
    )

    cols = list(df.columns)
    if not cols:
        st.info("No columns available.")
        return

    x = st.selectbox("X axis / category", cols, index=0)
    y: Optional[str] = None

    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]

    def _option_index(options: list[str], preferred: Optional[str] = None) -> int:
        if preferred and preferred in options:
            return options.index(preferred)
        return 0

    def _first_other(columns: list[str], skip: str) -> Optional[str]:
        for c in columns:
            if c != skip:
                return c
        return None

    if chart in {"Bar", "Line", "Scatter"}:
        y_candidates = [c for c in numeric_cols if c != x] or [c for c in cols if c != x] or cols
        y = st.selectbox(
            "Y axis (numeric recommended)",
            y_candidates,
            index=_option_index(y_candidates, _first_other(numeric_cols, x)),
        )
    elif chart == "Histogram":
        hist_candidates = numeric_cols or cols
        x = st.selectbox(
            "Column",
            hist_candidates,
            index=_option_index(hist_candidates, numeric_cols[0] if numeric_cols else None),
        )
    elif chart == "Pie":
        value_candidates = numeric_cols or [c for c in cols if c != x] or cols
        y = st.selectbox(
            "Values (numeric recommended)",
            value_candidates,
            index=_option_index(value_candidates, _first_other(numeric_cols, x)),
        )

    color = st.selectbox("Color (optional)", ["(none)"] + cols, index=0)
    color_col = None if color == "(none)" else color

    try:
        if chart == "Bar":
            fig = px.bar(df, x=x, y=y, color=color_col)
        elif chart == "Line":
            fig = px.line(df, x=x, y=y, color=color_col)
        elif chart == "Pie":
            fig = px.pie(df, names=x, values=y, color=color_col)
        elif chart == "Histogram":
            fig = px.histogram(df, x=x, color=color_col)
        else:  # Scatter
            fig = px.scatter(df, x=x, y=y, color=color_col)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not render chart: {e}")


def main() -> None:
    st.set_page_config(page_title="Smart Data Analysis", layout="wide")
    st.title("Smart Data Analysis and Visualization")

    st.sidebar.header("Data upload")
    upload = st.sidebar.file_uploader(
        "Upload a CSV/Excel file",
        type=["csv", "xlsx", "xls"],
        key="uploader",
    )

    if upload is None:
        st.info("Upload a CSV or Excel file from the sidebar to begin.")
        return

    raw_bytes = upload.getvalue()
    if not raw_bytes:
        st.error("Uploaded file is empty.")
        return

    upload_id = _upload_key(upload.name, raw_bytes)

    try:
        loaded = _read_upload(upload.name, raw_bytes)
    except Exception as e:
        st.error(str(e))
        return

    if st.session_state.get("upload_key") != upload_id:
        st.session_state["upload_key"] = upload_id
        st.session_state["raw_df"] = loaded.df
        st.session_state["raw_name"] = loaded.name
        st.session_state["pre_df"] = loaded.df.copy()
        st.session_state["filters"] = None

    raw_df: pd.DataFrame = st.session_state["raw_df"]

    pre_df: pd.DataFrame = st.session_state.get("pre_df", raw_df)
    spec = st.session_state.get("filters")
    filtered_df = apply_filters(pre_df, spec) if spec is not None else pre_df

    with st.sidebar:
        st.header("Current dataset")
        st.caption(f"Raw: {raw_df.shape[0]} × {raw_df.shape[1]}")
        st.caption(f"Preprocessed: {pre_df.shape[0]} × {pre_df.shape[1]}")
        st.caption(f"Filtered: {filtered_df.shape[0]} × {filtered_df.shape[1]}")
        if st.button("Reset preprocessing + filters", use_container_width=True):
            st.session_state["pre_df"] = raw_df.copy()
            st.session_state["filters"] = None
            st.rerun()

    tab_upload, tab_preprocess, tab_filter, tab_viz = st.tabs(
        ["Upload", "Preprocess", "Filter", "Visualize"]
    )

    with tab_upload:
        st.subheader("Preview")
        st.caption(f"File: {loaded.name} • Shape: {raw_df.shape[0]} rows × {raw_df.shape[1]} columns")
        st.dataframe(raw_df.head(20), use_container_width=True)

        st.subheader("Summary")
        st.write(raw_df.describe(include="all").transpose())

        num_sum = _numeric_summary(raw_df)
        if not num_sum.empty:
            st.subheader("Numeric summary (mean/median/etc.)")
            st.dataframe(num_sum, use_container_width=True)

    with tab_preprocess:
        st.subheader("Preprocessing")
        st.caption("Pick options below, then click Apply.")
        candidate = apply_preprocessing(raw_df)
        if st.button("Apply preprocessing", type="primary"):
            st.session_state["pre_df"] = candidate
            st.session_state["filters"] = None
            st.success("Preprocessing applied. Filters cleared.")
            st.rerun()

        st.subheader("Preview (current preprocessed dataset)")
        st.caption(f"Shape: {pre_df.shape[0]} rows × {pre_df.shape[1]} columns")
        st.dataframe(pre_df.head(20), use_container_width=True)

    with tab_filter:
        st.subheader("Filtering")
        st.caption("Create a filter and apply it. Visualizations use the filtered dataset.")
        candidate_spec = build_filter_spec(pre_df)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Apply filter", type="primary", use_container_width=True):
                st.session_state["filters"] = candidate_spec
                st.rerun()
        with c2:
            if st.button("Clear filters", use_container_width=True):
                st.session_state["filters"] = None
                st.rerun()

        st.subheader("Preview (current filtered dataset)")
        st.caption(f"Shape: {filtered_df.shape[0]} rows × {filtered_df.shape[1]} columns")
        st.dataframe(filtered_df.head(50), use_container_width=True)

    with tab_viz:
        _viz_panel(filtered_df)


if __name__ == "__main__":
    main()


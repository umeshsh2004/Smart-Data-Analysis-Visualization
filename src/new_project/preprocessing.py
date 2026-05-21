from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st


def apply_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    c1, c2 = st.columns(2)
    with c1:
        remove_dupes = st.checkbox("Remove duplicate rows", value=True)
    with c2:
        missing_strategy = st.selectbox(
            "Handle missing values",
            [
                "Do nothing",
                "Drop rows with any missing values",
                "Fill numeric with mean, non-numeric with mode",
                "Fill numeric with median, non-numeric with mode",
                "Fill everything with a constant",
            ],
            index=0,
        )

    if remove_dupes:
        before = len(working)
        working = working.drop_duplicates()
        st.caption(f"Removed {before - len(working)} duplicate rows.")

    if missing_strategy == "Do nothing":
        return working

    if missing_strategy == "Drop rows with any missing values":
        before = len(working)
        working = working.dropna(axis=0, how="any")
        st.caption(f"Dropped {before - len(working)} rows containing missing values.")
        return working

    if missing_strategy == "Fill everything with a constant":
        fill_value = st.text_input("Constant value", value="0")
        working = working.fillna(fill_value)
        return working

    numeric_cols = working.select_dtypes(include=[np.number]).columns.tolist()
    other_cols = [c for c in working.columns if c not in numeric_cols]

    if numeric_cols:
        if missing_strategy == "Fill numeric with mean, non-numeric with mode":
            means = working[numeric_cols].mean(numeric_only=True)
            working[numeric_cols] = working[numeric_cols].fillna(means)
        else:
            medians = working[numeric_cols].median(numeric_only=True)
            working[numeric_cols] = working[numeric_cols].fillna(medians)

    if other_cols:
        for c in other_cols:
            mode = working[c].mode(dropna=True)
            if len(mode) > 0:
                working[c] = working[c].fillna(mode.iloc[0])

    return working


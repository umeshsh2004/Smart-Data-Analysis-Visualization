from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd
import streamlit as st


@dataclass
class FilterSpec:
    column: str
    kind: str  # "categorical" | "numeric"
    values: Any


def _is_numeric(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)


def build_filter_spec(df: pd.DataFrame) -> Optional[FilterSpec]:
    if df.empty or df.shape[1] == 0:
        st.info("No data available to filter.")
        return None

    enabled = st.checkbox("Enable filtering", value=True)
    if not enabled:
        return None

    col = st.selectbox("Filter column", df.columns.tolist(), index=0)
    s = df[col]

    if _is_numeric(s):
        kind = "numeric"
        s_num = pd.to_numeric(s, errors="coerce")
        if not s_num.notna().any():
            st.warning("Selected column has no valid numeric values to filter on.")
            return None
        vmin = float(s_num.min())
        vmax = float(s_num.max())
        if vmin == vmax:
            st.caption("Selected numeric column has a single value; range filter won't change results.")
        lo, hi = st.slider("Range", min_value=vmin, max_value=vmax, value=(vmin, vmax))
        return FilterSpec(column=col, kind=kind, values=(lo, hi))

    kind = "categorical"
    options = sorted([x for x in s.dropna().astype(str).unique().tolist()])
    if not options:
        st.info("No non-null values in this column to filter on.")
        return None
    selected = st.multiselect("Keep values", options=options, default=options[: min(25, len(options))])
    if not selected:
        st.warning("Select at least one value to keep.")
        return None
    return FilterSpec(column=col, kind=kind, values=set(selected))


def apply_filters(df: pd.DataFrame, spec: Optional[FilterSpec]) -> pd.DataFrame:
    if spec is None:
        return df

    if spec.column not in df.columns:
        return df

    if spec.kind == "numeric":
        lo, hi = spec.values
        s = pd.to_numeric(df[spec.column], errors="coerce")
        return df[(s >= lo) & (s <= hi)]

    keep = spec.values
    s = df[spec.column].astype(str)
    return df[s.isin(keep)]


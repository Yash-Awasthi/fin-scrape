import pandas as pd
import streamlit as st

from gprobs.dashboard.contracts import (
    DATA_DIR,
    OUTPUT_SPECS,
    PROJECT_ROOT,
    REQUIRED_FILES,
    OutputSpec,
    validate_output_schema,
)

__all__ = [
    "DATA_DIR",
    "OUTPUT_SPECS",
    "PROJECT_ROOT",
    "REQUIRED_FILES",
    "OutputSpec",
    "load_outputs",
    "missing_files",
    "validate_output_schema",
]


@st.cache_data
def load_outputs():
    outputs = {}
    for name, spec in OUTPUT_SPECS.items():
        read_options = {}
        if spec.date_columns:
            read_options["parse_dates"] = list(spec.date_columns)
        if spec.low_memory is not None:
            read_options["low_memory"] = spec.low_memory
        output = pd.read_csv(spec.path, **read_options)
        validate_output_schema(output, spec)
        outputs[name] = output
    return outputs


def missing_files():
    return [path for path in REQUIRED_FILES.values() if not path.exists()]

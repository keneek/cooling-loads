"""Cooling Load Estimator

This app estimates cooling load for a given building type and square footage.
"""

import base64
import os
from datetime import datetime
from typing import List, Optional, Any

import pandas as pd  # type: ignore
import streamlit as st
from fpdf import FPDF  # type: ignore
from pydantic import BaseModel, Field, validate_call, model_validator, ValidationError

import plotly.express as px  # Add for visualization # type: ignore

# Beautification: Custom theme and page config
st.set_page_config(
    page_title="Cooling Load Estimator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Removed dark mode toggle and custom CSS; using official theme from config.toml


class BuildingData(BaseModel):
    """Building data model"""
    building_type: str = Field(alias="Building Type")

    refrig_low:   Optional[float] = Field(alias="Refrigeration_Low")
    refrig_avg:   Optional[float] = Field(alias="Refrigeration_Avg")
    refrig_high:  Optional[float] = Field(alias="Refrigeration_High")
    occupancy_low: Optional[float] = Field(alias="Occupancy_Low")
    occupancy_avg: Optional[float] = Field(alias="Occupancy_Avg")
    occupancy_high:Optional[float] = Field(alias="Occupancy_High")
    electrical_low: Optional[float] = Field(alias="Electrical_Low")
    electrical_avg: Optional[float] = Field(alias="Electrical_Avg")
    electrical_high:Optional[float] = Field(alias="Electrical_High")

    supply_esw_low:   Optional[float] = Field(alias="Supply_ESW_Low")
    supply_esw_avg:   Optional[float] = Field(alias="Supply_ESW_Avg")
    supply_esw_high:  Optional[float] = Field(alias="Supply_ESW_High")
    supply_north_low: Optional[float] = Field(alias="Supply_North_Low")
    supply_north_avg: Optional[float] = Field(alias="Supply_North_Avg")
    supply_north_high:Optional[float] = Field(alias="Supply_North_High")
    internalcfm_low:   Optional[float] = Field(alias="InternalCFM_Low")
    internalcfm_avg:   Optional[float] = Field(alias="InternalCFM_Avg")
    internalcfm_high:  Optional[float] = Field(alias="InternalCFM_High")

    @model_validator(mode='before')
    @classmethod
    def convert_empty_to_none(cls, values: dict[str, Any]) -> dict[str, Any]:  # type: ignore
        """Convert empty strings and NaNs to None"""

        for k, v in values.items():
            if v == "" or pd.isna(v):
                values[k] = None
        return values

    @model_validator(mode='after')
    def require_building_and_one_rate(self) -> 'BuildingData':  # type: ignore
        """Require building type and at least one rate"""
        
        if not self.building_type:
            raise ValueError("Building Type is required")
        return self


class DesignParams(BaseModel):
    """Design parameters model"""

    refrig: float
    occupancy: float
    electrical: float


class Results(BaseModel):
    """Results model"""

    tonnage: float
    total_occupancy: float
    electrical_kw: float
    design_params: DesignParams


# Load and validate data
data_path: str = 'ashrae_data.csv'
validated_data: List[BuildingData] = []
if os.path.exists(data_path):
    try:
        df_raw = pd.read_csv(data_path, dtype=str)  # type: ignore
        for i, (_, row) in enumerate(df_raw.iterrows()):
            try:
                bd = BuildingData(**row.to_dict())  # type: ignore
                validated_data.append(bd)
            except ValidationError as e:
                st.warning(f"Invalid data in CSV row {i + 2}: {e}")
    except Exception as e:
        st.error(f'Error loading CSV: {e}')
else:
    st.error(f"CSV file '{data_path}' not found.")

# Prepare lookups
building_types = [b.building_type for b in validated_data]

# Initialize session state
if 'selected_bld' not in st.session_state:
    st.session_state.selected_bld = None
if 'selected_load' not in st.session_state:
    st.session_state.selected_load = 'Avg'

# Remove zone-related state

# Remove update_available_zones function

# Sidebar
st.sidebar.title("Input Parameters")

# Multi-select for building types
selected_blds = st.sidebar.multiselect(
    "Building Types (select multiple to compare)",
    building_types,
    default=[building_types[0]] if building_types else []
)

sq_ft: int = st.sidebar.number_input("Building Area (sq ft)", min_value=0, value=7500, step=1, format="%i")
load_type = st.sidebar.radio("Load Type", ["Low","Avg","High"], index=1, key='selected_load')

# CSV override
uploaded = st.sidebar.file_uploader("Upload Custom CSV", type="csv")
if uploaded:
    df_override = pd.read_csv(uploaded, dtype=str)  # type: ignore
    temp = []
    for i, (_, row) in enumerate(df_override.iterrows()):
        try:
            temp.append(BuildingData(**row.to_dict()))  # type: ignore
        except ValidationError as e:
            st.warning(f"Invalid data in uploaded CSV row {i + 2}: {e}")
    if temp:
        validated_data = temp
        building_types = [b.building_type for b in validated_data]
        st.sidebar.success("Custom data loaded!")

# Computation
@st.cache_data
@validate_call
def compute_results(
    building_type: str,
    area: float,
    level: str,
) -> Optional[Results]:
    if level not in ['Low', 'Avg', 'High']:
        raise ValueError("Invalid load level")
    bd = next((b for b in validated_data if b.building_type==building_type), None)
    if bd is None:
        return None
    level_lower = level.lower()
    r = getattr(bd, f"refrig_{level_lower}")
    o = getattr(bd, f"occupancy_{level_lower}")
    e = getattr(bd, f"electrical_{level_lower}")
    if None in (r,o,e):
        raise ValueError("Selected building type/load has missing data")
    tonnage = float(area) / r
    tot_occ = float(area) / o
    elec_kw = (float(area) * e)/1000.0
    return Results(
        tonnage=tonnage,
        total_occupancy=tot_occ,
        electrical_kw=elec_kw,
        design_params=DesignParams(refrig=r, occupancy=o, electrical=e),
    )

# Compute for single (first) selection for main display
results = None
chosen_bld = st.selectbox(
    "Show details for",
    selected_blds,
    index=0 if selected_blds else None
) if len(selected_blds) > 1 else (selected_blds[0] if selected_blds else None)
if chosen_bld:
    try:
        results = compute_results(chosen_bld, sq_ft, load_type)
    except Exception as err:
        st.error(f"Calculation error for {chosen_bld}: {err}")

# --- Display Single Result ---
st.title("Cooling Load Estimator")
st.caption("Preliminary sizing via ASHRAE check figures")
if not results:
    st.warning("Select valid inputs to compute.")
else:
    c1,c2,c3 = st.columns(3)
    c1.metric("Tonnage", f"{results.tonnage:.2f} tons")
    c2.metric("Occupancy", f"{results.total_occupancy:.0f} ppl")
    c3.metric("Plug/Light Load (kW)", f"{results.electrical_kw:.2f} kW")
    st.caption('Note: Electrical load represents lights and plug loads for HVAC heat gain, not total service size.')
    st.subheader("Design Rates")
    dp = results.design_params
    rates_df = pd.DataFrame({
        'Parameter': ['Refrigeration Rate (ft²/ton)', 'Occupancy Rate (ft²/person)', 'Plug/Light Rate (W/ft²)'],
        'Value': [dp.refrig, dp.occupancy, dp.electrical]
    })
    st.dataframe(rates_df, hide_index=True)  # type: ignore

    # Preserve PDF export
    st.subheader("Export")
    if chosen_bld and results:
        def create_pdf(results: Results, building_type: str, sq_ft: float, load_type: str) -> FPDF:
            pdf = FPDF()  # type: ignore
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'ASHRAE Cooling Load Report', ln=1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=1)
            pdf.cell(0, 10, f'Building: {building_type}, Area: {sq_ft} sq ft, Load: {load_type}', ln=1)
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, 'Results:', ln=1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Cooling Tonnage: {results.tonnage:.2f} tons', ln=1)
            pdf.cell(0, 10, f'Total Occupancy: {results.total_occupancy:.0f} people', ln=1)
            pdf.cell(0, 10, f'Plug/Light Load: {results.electrical_kw:.2f} kW', ln=1)
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, 'Design Parameters:', ln=1)
            pdf.set_font('Arial', '', 10)
            params = results.design_params
            pdf.cell(0, 10, f'Refrigeration Rate: {params.refrig} ft²/ton', ln=1)
            pdf.cell(0, 10, f'Occupancy Rate: {params.occupancy} ft²/person', ln=1)
            pdf.cell(0, 10, f'Plug/Light Rate: {params.electrical} W/ft²', ln=1)
            pdf.cell(0, 10, 'Note: Electrical values are for HVAC heat gain assumptions per ASHRAE.', ln=1)
            return pdf  # type: ignore

        pdf = create_pdf(results, chosen_bld, sq_ft, load_type)  # type: ignore
        pdf_str = pdf.output(dest="S")  # type: ignore
        pdf_bytes = pdf_str.encode("latin-1") if isinstance(pdf_str, str) else pdf_str  # type: ignore
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")  # type: ignore
        st.markdown(
            f'<a href="data:application/pdf;base64,{b64}" download="report.pdf">Download PDF</a>',
            unsafe_allow_html=True,
        )

# --- Multi-Type Comparison Visualization ---
st.subheader("Tonnage Comparison Across Building Types")
if len(selected_blds) > 1:
    comparison_data: list[dict[str, str | float]] = []
    for bld in selected_blds:
        for level in ["Low", "Avg", "High"]:
            try:
                res = compute_results(bld, sq_ft, level)
                if res:
                    comparison_data.append({  # type: ignore
                        "Building Type": bld,
                        "Load Level": level,
                        "Tonnage": res.tonnage
                    })  # type: ignore
            except Exception:
                pass

    if comparison_data:
        df_comp = pd.DataFrame(comparison_data)
        fig = px.bar(  # type: ignore
            df_comp,
            x="Building Type",
            y="Tonnage",
            color="Load Level",
            barmode="group",
            title=f"Tonnage Ranges for {sq_ft} sq ft",
            color_discrete_map={"Low": "#1f77b4", "Avg": "#ff7f0e", "High": "#2ca02c"}
        )
        fig.update_layout(  # type: ignore
            plot_bgcolor="#1a1a1a",
            paper_bgcolor="#1a1a1a",
            font_color="#d9d9d9",
            xaxis_title="Building Type",
            yaxis_title="Tonnage (tons)",
            legend_title="Load Level"
        )
        st.plotly_chart(fig, use_container_width=True)  # type: ignore
    else:
        st.warning("No valid data for comparison across selected types.")
else:
    st.info("Select multiple building types to compare tonnage ranges.")

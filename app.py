"""Cooling Load Estimator

This app estimates cooling load for a given building type and square footage.
"""

import base64
import json
import os
from datetime import datetime
from typing import Any, List, Optional

import boto3
import pandas as pd  # type: ignore
import plotly.express as px  # Add for visualization # type: ignore
import streamlit as st
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from fpdf import FPDF  # type: ignore
from pydantic import BaseModel, Field, ValidationError, model_validator, validate_call

try:
    from dotenv import load_dotenv
    import os.path
    
    if os.path.exists('.env'):
        load_dotenv()  # Load environment variables from .env file if it exists
        print("✅ Loaded environment variables from .env file")
    else:
        print("ℹ️  No .env file found, using system environment variables")
except ImportError:
    print("ℹ️  python-dotenv not installed, using system environment variables")

# AWS Cognito configuration - these will come from CDK outputs
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'CoolingProjects')

# Check for required environment variables
if not COGNITO_USER_POOL_ID or not COGNITO_CLIENT_ID:
    st.error("""
    ⚠️ **Missing AWS Configuration!**
    
    For local development, you need to set these environment variables:
    
    ```bash
    export COGNITO_USER_POOL_ID=us-east-1_m90QdkzAE
    export COGNITO_CLIENT_ID=9femh6tcf9na3e32ecrbvv531
    export DYNAMODB_TABLE_NAME=StreamlitStack-CoolingProjectsTable0EA00323-11DPLBS3H8FEF
    export AWS_DEFAULT_REGION=us-east-1
    ```
    
    Then restart Streamlit with: `poetry run streamlit run app.py`
    
    Also ensure you have AWS credentials configured via:
    - `aws sso login --profile prodAdmin` (then `export AWS_PROFILE=prodAdmin`)
    - Or `aws configure` for regular credentials
    """)
    st.stop()

# Initialize AWS clients
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Authentication functions
def sign_up(username, password, email):
    try:
        response = cognito_client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[{'Name': 'email', 'Value': email}]
        )
        return True, "Sign up successful! Please check your email for verification code."
    except ClientError as e:
        return False, str(e)

def confirm_sign_up(username, code):
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=username,
            ConfirmationCode=code
        )
        return True, "Account confirmed!"
    except ClientError as e:
        return False, str(e)

def sign_in(username, password):
    try:
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        st.session_state['access_token'] = response['AuthenticationResult']['AccessToken']
        st.session_state['username'] = username
        return True, "Logged in successfully!"
    except ClientError as e:
        return False, str(e)

def save_project(project_name, range_results, selected_building_types, current_building_type, square_footage):
    if 'access_token' not in st.session_state:
        return False, "Please log in to save projects"

    try:
        # Check if this is an update to an existing project
        is_update = False
        created_at = datetime.now().isoformat()
        
        # Try to get existing project to preserve creation date
        try:
            response = table.get_item(
                Key={
                    'username': st.session_state['username'],
                    'project_name': project_name
                }
            )
            if 'Item' in response:
                existing_config = json.loads(response['Item']['config'])
                created_at = existing_config.get('created_at', created_at)
                is_update = True
        except:
            pass  # If we can't get existing project, treat as new
        
        now = datetime.now().isoformat()
        
        # Debug: Print the square footage being saved
        print(f"DEBUG save_project: square_footage parameter = {square_footage}")
        print(f"DEBUG save_project: type = {type(square_footage)}")
        
        project_config = ProjectConfig(
            project_name=project_name,
            selected_building_types=selected_building_types,
            current_building_type=current_building_type,
            square_footage=square_footage,
            range_results=range_results,
            created_at=created_at,
            updated_at=now
        )
        
        table.put_item(
            Item={
                'username': st.session_state['username'],
                'project_name': project_name,
                'config': json.dumps(project_config.dict()),
                'created_at': created_at,
                'updated_at': now
            }
        )
        
        action = "updated" if is_update else "saved"
        return True, f"Project {action}!"
    except ClientError as e:
        return False, str(e)

def load_project_config(project_name):
    """Load and restore a project configuration"""
    if 'access_token' not in st.session_state:
        return False, "Please log in to load projects"
    
    try:
        response = table.get_item(
            Key={
                'username': st.session_state['username'],
                'project_name': project_name
            }
        )
        
        if 'Item' in response:
            config_data = json.loads(response['Item']['config'])
            project_config = ProjectConfig(**config_data)
            
            # Restore session state (but NOT widget states - that causes Streamlit errors)
            st.session_state['loaded_selected_blds'] = project_config.selected_building_types
            st.session_state['loaded_current_bld'] = project_config.current_building_type
            st.session_state['loaded_sq_ft'] = project_config.square_footage
            st.session_state['project_loaded'] = True
            st.session_state['loaded_project_name'] = project_name
            
            # Flag for rerun to reset widgets properly
            st.session_state['need_widget_reset'] = True
            
            return True, f"Project '{project_name}' loaded successfully!"
        else:
            return False, "Project not found"
            
    except ClientError as e:
        return False, str(e)

def delete_project(project_name):
    """Delete a project"""
    if 'access_token' not in st.session_state:
        return False, "Please log in to delete projects"
    
    try:
        # Debug: Show what we're trying to delete
        username = st.session_state['username']
        print(f"Attempting to delete project: {project_name} for user: {username}")
        
        response = table.delete_item(
            Key={
                'username': username,
                'project_name': project_name
            }
        )
        
        # Debug: Show response
        print(f"Delete response: {response}")
        return True, f"Project '{project_name}' deleted successfully!"
    except ClientError as e:
        print(f"Delete error: {str(e)}")
        return False, str(e)
    except Exception as e:
        print(f"Unexpected delete error: {str(e)}")
        return False, f"Unexpected error: {str(e)}"

def load_projects():
    if 'access_token' not in st.session_state:
        return None

    try:
        response = table.query(
            KeyConditionExpression=Key('username').eq(st.session_state['username'])
        )
        return response['Items']
    except ClientError as e:
        st.error(str(e))
        return None

# Beautification: Custom theme and page config
st.set_page_config(
    page_title="Cooling Load Estimator",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom HTML meta tags for social media sharing
st.html("""
<meta property="og:title" content="Cooling Load Estimator" />
<meta property="og:description" content="Professional HVAC cooling load calculator. Calculate tonnage, occupancy, and electrical loads for various building types." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://loadestimator.com" />
<meta property="og:site_name" content="Load Estimator" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="Cooling Load Estimator" />
<meta name="twitter:description" content="Professional HVAC cooling load calculator based. Calculate tonnage, occupancy, and electrical loads for various building types." />
<meta name="description" content="Professional HVAC cooling load calculator based on category and square footage. Calculate tonnage, occupancy, and electrical loads for various building types." />
<meta name="author" content="Load Estimator" />
""")

# Add mobile-responsive CSS
st.markdown("""
<style>
    /* Mobile-responsive improvements */
    @media (max-width: 768px) {
        /* Improve sidebar width on mobile */
        section[data-testid="stSidebar"] {
            width: 85% !important;
            max-width: 350px !important;
        }
        
        /* Larger touch targets for mobile */
        button[kind="primary"], button[kind="secondary"] {
            min-height: 48px !important;
            font-size: 16px !important;
            padding: 12px 24px !important;
        }
        
        /* Better form input styling for mobile */
        input[type="text"], input[type="password"], input[type="email"] {
            font-size: 16px !important;
            padding: 12px !important;
            min-height: 48px !important;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
        }
        
        /* Improve tab navigation on mobile */
        div[data-testid="stTabs"] button {
            font-size: 16px !important;
            padding: 10px 16px !important;
            min-height: 44px !important;
        }
        
        /* Better spacing for mobile forms */
        div[data-testid="stForm"] {
            padding: 16px !important;
        }
        
        /* Ensure form submit buttons are full width on mobile */
        div[data-testid="stForm"] button[type="submit"] {
            width: 100% !important;
            min-height: 48px !important;
            font-size: 16px !important;
            margin-top: 8px !important;
        }
        
        /* Improve metric display on mobile */
        div[data-testid="metric-container"] {
            padding: 12px !important;
        }
        
        /* Better button spacing */
        div.stButton > button {
            margin-bottom: 8px !important;
        }
    }
    
    /* General improvements for all devices */
    /* Ensure inputs don't zoom on focus (iOS) */
    input[type="text"], input[type="password"], input[type="email"] {
        font-size: 16px !important;
    }
    
    /* Improve form labels */
    label {
        font-size: 14px !important;
        font-weight: 500 !important;
        margin-bottom: 4px !important;
    }
    
    /* Better error/success message styling */
    div.stAlert {
        padding: 12px 16px !important;
        font-size: 14px !important;
    }
    
    /* Additional mobile improvements */
    @media (max-width: 768px) {
        /* Make columns stack on mobile for auth buttons */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
        }
        
        /* Add spacing between stacked buttons */
        div[data-testid="column"]:not(:last-child) {
            margin-bottom: 8px !important;
        }
        
        /* Ensure forms are scrollable on small screens */
        section[data-testid="stSidebar"] > div {
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
    }
    
    /* Prevent text selection on buttons */
    button {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
        -webkit-tap-highlight-color: transparent;
    }
    
    /* Improve focus states */
    input:focus, button:focus {
        outline: 2px solid #4da6ff !important;
        outline-offset: 2px !important;
    }
</style>
""", unsafe_allow_html=True)

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

class RangeResults(BaseModel):
    """Results model for all three load levels"""
    
    low: Results
    avg: Results
    high: Results

class ProjectConfig(BaseModel):
    """Complete project configuration model"""
    
    project_name: str
    selected_building_types: List[str]
    current_building_type: str
    square_footage: int
    range_results: RangeResults
    created_at: str
    updated_at: str


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
if 'project_loaded' not in st.session_state:
    st.session_state['project_loaded'] = False
if 'loaded_selected_blds' not in st.session_state:
    st.session_state['loaded_selected_blds'] = []
if 'loaded_current_bld' not in st.session_state:
    st.session_state['loaded_current_bld'] = None
if 'loaded_sq_ft' not in st.session_state:
    st.session_state['loaded_sq_ft'] = 7500
if 'loaded_project_name' not in st.session_state:
    st.session_state['loaded_project_name'] = None
if 'show_save_as_new' not in st.session_state:
    st.session_state['show_save_as_new'] = False

# Remove zone-related state

# Remove update_available_zones function

# Sidebar
st.sidebar.title("Input Parameters")

# Multi-select for building types - handle loaded project state properly
if st.session_state.get('project_loaded') and st.session_state.get('need_widget_reset'):
    # Clear existing widget states to allow reset
    if 'selected_buildings' in st.session_state:
        del st.session_state['selected_buildings']
    if 'square_footage' in st.session_state:
        del st.session_state['square_footage']
    st.session_state['need_widget_reset'] = False

# Set defaults based on loaded project or use defaults
if st.session_state.get('project_loaded'):
    default_selected = st.session_state.get('loaded_selected_blds', ["Office Buildings (General)"])
    default_sq_ft = st.session_state.get('loaded_sq_ft', 7500)
else:
    default_selected = ["Office Buildings (General)"] if "Office Buildings (General)" in building_types else ([building_types[0]] if building_types else [])
    default_sq_ft = 7500

selected_blds = st.sidebar.multiselect(
    "Building Types (select multiple to compare)",
    building_types,
    default=default_selected,
    key="selected_buildings"
)

sq_ft: int = st.sidebar.number_input("Building Area (sq ft)", min_value=0, value=default_sq_ft, step=1, format="%i", key="square_footage")

# We'll add project management controls after calculations are done

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
    """Compute results for a given building type, area, and load level"""
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

@st.cache_data
@validate_call
def compute_range_results(
    building_type: str,
    area: float,
) -> Optional[RangeResults]:
    """Compute results for all three load levels (Low, Avg, High)"""
    try:
        low_result = compute_results(building_type, area, "Low")
        avg_result = compute_results(building_type, area, "Avg")
        high_result = compute_results(building_type, area, "High")
        
        if None in (low_result, avg_result, high_result):
            return None
            
        return RangeResults(
            low=low_result,
            avg=avg_result,
            high=high_result
        )
    except Exception:
        return None

# Compute for single (first) selection for main display
range_results = None
if len(selected_blds) > 1:
    # If project was loaded, try to select the loaded current building
    if st.session_state.get('project_loaded') and st.session_state['loaded_current_bld'] in selected_blds:
        default_index = selected_blds.index(st.session_state['loaded_current_bld'])
    else:
        default_index = 0
    
    chosen_bld = st.selectbox(
        "Show details for",
        selected_blds,
        index=default_index if selected_blds else None
    )
else:
    chosen_bld = selected_blds[0] if selected_blds else None
if chosen_bld:
    try:
        range_results = compute_range_results(chosen_bld, sq_ft)
    except Exception as err:
        st.error(f"Calculation error for {chosen_bld}: {err}")

# --- Display Range Results ---
st.title("Cooling Load Estimator")

# Show loaded project indicator in main panel
if st.session_state.get('project_loaded') and st.session_state.get('loaded_project_name'):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.info(f"📂 **Working on Project:** {st.session_state['loaded_project_name']}")
    with col2:
        if st.button("✖️ Clear", help="Clear loaded project and start fresh", key="main_clear_project"):
            st.session_state['project_loaded'] = False
            st.session_state['loaded_project_name'] = None
            # Clear widget states properly (don't set directly - causes Streamlit errors)
            if 'selected_buildings' in st.session_state:
                del st.session_state['selected_buildings']
            if 'square_footage' in st.session_state:
                del st.session_state['square_footage']
            st.rerun()

if chosen_bld:
    st.subheader(f"📋 {chosen_bld}")
st.caption("Preliminary sizing estimates")
if not range_results:
    st.warning("Select valid inputs to compute.")
else:
    # Show the main metrics with average emphasized and range shown
    c1, c2, c3 = st.columns(3)
    
    # Tonnage with range
    avg_tonnage = range_results.avg.tonnage
    low_tonnage = range_results.low.tonnage
    high_tonnage = range_results.high.tonnage
    c1.metric(
        "Tonnage", 
        f"{avg_tonnage:.1f} tons",
        delta=f"Range: {low_tonnage:.1f} - {high_tonnage:.1f} tons"
    )
    
    # Occupancy with range
    avg_occ = range_results.avg.total_occupancy
    low_occ = range_results.low.total_occupancy
    high_occ = range_results.high.total_occupancy
    c2.metric(
        "Occupancy", 
        f"{avg_occ:.0f} people",
        delta=f"Range: {low_occ:.0f} - {high_occ:.0f} people"
    )
    
    # Electrical with range
    avg_elec = range_results.avg.electrical_kw
    low_elec = range_results.low.electrical_kw
    high_elec = range_results.high.electrical_kw
    c3.metric(
        "Plug/Light Load", 
        f"{avg_elec:.1f} kW",
        delta=f"Range: {low_elec:.1f} - {high_elec:.1f} kW"
    )
    
    st.caption('Note: **Average values** are shown prominently with full range below. Electrical load represents lights and plug loads for HVAC heat gain, not total service size.')
    
    # Show detailed breakdown
    st.subheader("Load Level Breakdown")
    breakdown_df = pd.DataFrame({
        'Load Level': ['Low', 'Average', 'High'],
        'Tonnage': [f"{low_tonnage:.2f}", f"{avg_tonnage:.2f}", f"{high_tonnage:.2f}"],
        'Occupancy': [f"{low_occ:.0f}", f"{avg_occ:.0f}", f"{high_occ:.0f}"],
        'Electrical (kW)': [f"{low_elec:.2f}", f"{avg_elec:.2f}", f"{high_elec:.2f}"]
    })
    st.dataframe(breakdown_df, hide_index=True)  # type: ignore
    
    st.subheader("Design Rates")
    rates_df = pd.DataFrame({
        'Load Level': ['Low', 'Average', 'High'],
        'Refrigeration Rate (ft²/ton)': [range_results.low.design_params.refrig, range_results.avg.design_params.refrig, range_results.high.design_params.refrig],
        'Occupancy Rate (ft²/person)': [range_results.low.design_params.occupancy, range_results.avg.design_params.occupancy, range_results.high.design_params.occupancy],  
        'Plug/Light Rate (W/ft²)': [range_results.low.design_params.electrical, range_results.avg.design_params.electrical, range_results.high.design_params.electrical]
    })
    st.dataframe(rates_df, hide_index=True)  # type: ignore

    # Preserve PDF export
    st.subheader("Export")
    if chosen_bld and range_results:
        def create_pdf(range_results: RangeResults, building_type: str, sq_ft: float) -> FPDF:
            pdf = FPDF()  # type: ignore
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Cooling Load Estimator Report', ln=1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=1)
            pdf.cell(0, 10, f'Building: {building_type}, Area: {sq_ft} sq ft', ln=1)
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, 'Results Summary (Average Values):', ln=1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Cooling Tonnage: {range_results.avg.tonnage:.2f} tons', ln=1)
            pdf.cell(0, 10, f'Total Occupancy: {range_results.avg.total_occupancy:.0f} people', ln=1)
            pdf.cell(0, 10, f'Plug/Light Load: {range_results.avg.electrical_kw:.2f} kW', ln=1)
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, 'Load Range Analysis:', ln=1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Tonnage Range: {range_results.low.tonnage:.2f} - {range_results.high.tonnage:.2f} tons', ln=1)
            pdf.cell(0, 10, f'Occupancy Range: {range_results.low.total_occupancy:.0f} - {range_results.high.total_occupancy:.0f} people', ln=1)
            pdf.cell(0, 10, f'Electrical Range: {range_results.low.electrical_kw:.2f} - {range_results.high.electrical_kw:.2f} kW', ln=1)
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, 'Design Parameters (Average):', ln=1)
            pdf.set_font('Arial', '', 10)
            params = range_results.avg.design_params
            pdf.cell(0, 10, f'Refrigeration Rate: {params.refrig} ft²/ton', ln=1)
            pdf.cell(0, 10, f'Occupancy Rate: {params.occupancy} ft²/person', ln=1)
            pdf.cell(0, 10, f'Plug/Light Rate: {params.electrical} W/ft²', ln=1)
            pdf.cell(0, 10, 'Note: Electrical values are estimated plug load and other equipment for HVAC heat gain assumptions.', ln=1)
            return pdf  # type: ignore

        pdf = create_pdf(range_results, chosen_bld, sq_ft)  # type: ignore
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

# === SIDEBAR AUTHENTICATION & PROJECT MANAGEMENT ===
with st.sidebar:
    st.title("🔐 Account")
    
    # Initialize session state for authentication
    if 'access_token' not in st.session_state:
        st.session_state['access_token'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'show_auth_form' not in st.session_state:
        st.session_state['show_auth_form'] = False
    if 'auth_source' not in st.session_state:
        st.session_state['auth_source'] = None
    
    # User status and authentication
    if st.session_state.get('access_token'):
        # Logged in user UI
        st.success(f"👋 **{st.session_state['username']}**")
        if st.button("🚪 Sign Out", use_container_width=True, type="primary"):
            st.session_state['access_token'] = None
            st.session_state['username'] = None
            st.session_state['show_auth_form'] = False
            st.rerun()
        
        st.divider()
        st.subheader("🔐 Project Management")
        
        # Show loaded project indicator if applicable
        if st.session_state.get('project_loaded') and st.session_state.get('loaded_project_name'):
            st.success(f"📂 Loaded: {st.session_state['loaded_project_name']}")
            
            # Update/Save controls
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("📝 Update", use_container_width=True, type="primary"):
                    if range_results:
                        success, message = save_project(
                            st.session_state['loaded_project_name'], 
                            range_results, 
                            selected_blds, 
                            chosen_bld, 
                            st.session_state['square_footage']  # Use actual widget state
                        )
                        if success:
                            st.success("✅ Updated!")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            with col2:
                if st.button("💾 Save As", use_container_width=True):
                    st.session_state['show_save_as_new'] = True
                    st.rerun()
            
            if st.button("✖️ Clear Loaded Project", use_container_width=True):
                st.session_state['project_loaded'] = False
                st.session_state['loaded_project_name'] = None
                # Clear widget states properly (don't set directly - causes Streamlit errors)
                if 'selected_buildings' in st.session_state:
                    del st.session_state['selected_buildings']
                if 'square_footage' in st.session_state:
                    del st.session_state['square_footage']
                st.rerun()
        
        else:
            # No project loaded - show save new project
            st.markdown("**💾 Save New Project**")
            project_name = st.text_input("Project Name", placeholder="Enter project name...", key="sidebar_project_name")
            if st.button("💾 Save Project", use_container_width=True, type="primary"):
                if project_name and range_results:
                    # Debug: Print the actual values being saved
                    print(f"DEBUG: Saving project with square_footage = {st.session_state['square_footage']}")
                    print(f"DEBUG: selected_blds = {selected_blds}")
                    print(f"DEBUG: chosen_bld = {chosen_bld}")
                    
                    success, message = save_project(
                        project_name, 
                        range_results, 
                        selected_blds, 
                        chosen_bld, 
                        st.session_state['square_footage']  # Use actual widget state
                    )
                    if success:
                        st.success("✅ Saved!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                elif not project_name:
                    st.warning("⚠️ Enter project name")
                elif not range_results:
                    st.warning("⚠️ Select building type first")
        
        # Handle "Save as New" dialog
        if st.session_state.get('show_save_as_new'):
            st.divider()
            st.markdown("**💾 Save as New Project**")
            new_project_name = st.text_input("New Project Name", placeholder="Enter new name...", key="sidebar_new_project_name")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 Save", use_container_width=True, type="primary"):
                    if new_project_name and range_results:
                        success, message = save_project(
                            new_project_name, 
                            range_results, 
                            selected_blds, 
                            chosen_bld, 
                            st.session_state['square_footage']
                        )
                        if success:
                            st.success("✅ Saved!")
                            st.session_state['show_save_as_new'] = False
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.warning("⚠️ Enter name")
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state['show_save_as_new'] = False
                    st.rerun()

        st.divider()
        st.subheader("📁 Your Projects")
        
        # Load and display user projects
        projects = load_projects()
        if projects:
            for project in projects:
                # Parse project config for preview
                try:
                    project_name = project['project_name']
                    created_date = project.get('created_at', 'Unknown date')[:10] if project.get('created_at') else 'Unknown date'
                    
                    # Check if this is new format (has 'config') or old format (has 'results')
                    if 'config' in project:
                        # New format with full config
                        config_data = json.loads(project['config'])
                        building_type = config_data.get('current_building_type', 'Unknown')
                        sq_ft = config_data.get('square_footage', 0)
                        avg_tonnage = config_data['range_results']['avg']['tonnage']
                        preview_text = f"📅 {created_date}"
                        detail_text = f"{building_type} • {sq_ft:,} sq ft • {avg_tonnage:.1f} tons"
                        is_legacy = False
                    elif 'results' in project:
                        # Old format - extract from results
                        results_data = json.loads(project['results'])
                        tonnage = results_data.get('tonnage', 0)
                        occupancy = results_data.get('total_occupancy', 0)
                        electrical = results_data.get('electrical_kw', 0)
                        preview_text = f"📅 {created_date} • Legacy Format"
                        detail_text = f"{tonnage:.1f} tons • {occupancy:.0f} people • {electrical:.1f} kW"
                        is_legacy = True
                    else:
                        preview_text = "Invalid project data"
                        detail_text = ""
                        is_legacy = False
                        
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    created_date = project.get('created_at', 'Unknown date')[:10] if project.get('created_at') else 'Unknown date'
                    preview_text = f"📅 {created_date} • Error loading project"
                    detail_text = "Unable to parse project data"
                    is_legacy = False
                
                # Project container
                with st.container():
                    st.markdown(f"**📊 {project_name}**")
                    st.caption(preview_text)
                    if detail_text:
                        st.markdown(f"*{detail_text}*")
                    
                    # Action buttons - Load and Delete only (removed View)
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        # Disable load for legacy projects since they don't have full config
                        load_disabled = is_legacy
                        load_help = "⚠️ Cannot load legacy projects (missing configuration data)" if is_legacy else None
                        
                        if st.button("📂 Load", key=f"load_{project_name}", use_container_width=True, 
                                   type="primary", disabled=load_disabled, help=load_help):
                            success, message = load_project_config(project_name)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    with col2:
                        # Check if this project is in confirmation state
                        confirm_key = f'confirm_delete_{project_name}'
                        if st.session_state.get(confirm_key, False):
                            # Show confirmation buttons
                            subcol1, subcol2 = st.columns([1, 1])
                            with subcol1:
                                if st.button("✅ Yes", key=f"confirm_yes_{project_name}", use_container_width=True, type="primary"):
                                    success, message = delete_project(project_name)
                                    st.session_state[confirm_key] = False  # Clear confirmation state
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                            with subcol2:
                                if st.button("❌ No", key=f"confirm_no_{project_name}", use_container_width=True):
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                        else:
                            # Show delete button
                            if st.button("🗑️ Delete", key=f"delete_{project_name}", use_container_width=True):
                                # Clear any other confirmations and set this one
                                for other_project in projects:
                                    other_confirm_key = f'confirm_delete_{other_project["project_name"]}'
                                    if other_confirm_key != confirm_key:
                                        st.session_state[other_confirm_key] = False
                                st.session_state[confirm_key] = True
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("💡 No saved projects yet")
    
    else:
        # Guest user UI
        st.info("👤 **Guest Mode**")
        st.caption("Sign in to save and manage projects")
        
        if st.button("🔑 Sign In / Sign Up", use_container_width=True, type="primary"):
            st.session_state['show_auth_form'] = not st.session_state.get('show_auth_form', False)
            st.session_state['auth_source'] = 'sidebar'
        
        # Authentication form (collapsible)
        if st.session_state.get('show_auth_form'):
            st.divider()
            auth_tab1, auth_tab2, auth_tab3 = st.tabs(["Sign In", "Sign Up", "Confirm"])
            
            with auth_tab1:
                with st.form("signin_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    signin_submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                    
                    if signin_submitted and username and password:
                        success, message = sign_in(username, password)
                        if success:
                            st.session_state['show_auth_form'] = False
                            st.session_state['auth_source'] = None
                            st.success("✅ Signed in!")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
            with auth_tab2:
                with st.form("signup_form"):
                    signup_username = st.text_input("Username", placeholder="Choose a username", key="signup_user")
                    signup_email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
                    signup_password = st.text_input("Password", type="password", placeholder="Min 8 chars, 1 uppercase, 1 number", key="signup_pass")
                    st.caption("Password must be at least 8 characters with 1 uppercase letter and 1 number")
                    signup_submitted = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
                    
                    if signup_submitted and signup_username and signup_email and signup_password:
                        success, message = sign_up(signup_username, signup_password, signup_email)
                        if success:
                            st.success("✅ Account created! Check your email for verification code.")
                        else:
                            st.error(f"❌ {message}")
            
            with auth_tab3:
                with st.form("confirm_form"):
                    confirm_username = st.text_input("Username", placeholder="Your username", key="confirm_user")
                    confirm_code = st.text_input("Verification Code", placeholder="Check your email", key="confirm_code")
                    st.caption("Enter the 6-digit code from your email")
                    confirm_submitted = st.form_submit_button("Confirm Account", use_container_width=True, type="primary")
                    
                    if confirm_submitted and confirm_username and confirm_code:
                        success, message = confirm_sign_up(confirm_username, confirm_code)
                        if success:
                            st.success("✅ Account confirmed! You can now sign in.")
                        else:
                            st.error(f"❌ {message}")

# === AUTHENTICATION FORM IN MAIN AREA (for mobile) ===
if st.session_state.get('show_auth_form') and st.session_state.get('auth_source') == 'main':
    st.divider()
    st.subheader("🔐 Authentication")
    
    # Show the auth form here for convenience
    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["Sign In", "Sign Up", "Confirm"])
    
    with auth_tab1:
        with st.form("main_signin_form"):
            username = st.text_input("Username", placeholder="Enter your username", key="main_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="main_password")
            signin_submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            
            if signin_submitted and username and password:
                success, message = sign_in(username, password)
                if success:
                    st.session_state['show_auth_form'] = False
                    st.session_state['auth_source'] = None
                    st.success("✅ Signed in!")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with auth_tab2:
        with st.form("main_signup_form"):
            signup_username = st.text_input("Username", placeholder="Choose a username", key="main_signup_user")
            signup_email = st.text_input("Email", placeholder="your@email.com", key="main_signup_email")
            signup_password = st.text_input("Password", type="password", placeholder="Min 8 chars, 1 uppercase, 1 number", key="main_signup_pass")
            st.caption("Password must be at least 8 characters with 1 uppercase letter and 1 number")
            signup_submitted = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
            
            if signup_submitted and signup_username and signup_email and signup_password:
                success, message = sign_up(signup_username, signup_password, signup_email)
                if success:
                    st.success("✅ Account created! Check your email for verification code.")
                else:
                    st.error(f"❌ {message}")
    
    with auth_tab3:
        with st.form("main_confirm_form"):
            confirm_username = st.text_input("Username", placeholder="Your username", key="main_confirm_user")
            confirm_code = st.text_input("Verification Code", placeholder="Check your email", key="main_confirm_code")
            st.caption("Enter the 6-digit code from your email")
            confirm_submitted = st.form_submit_button("Confirm Account", use_container_width=True, type="primary")
            
            if confirm_submitted and confirm_username and confirm_code:
                success, message = confirm_sign_up(confirm_username, confirm_code)
                if success:
                    st.success("✅ Account confirmed! You can now sign in.")
                else:
                    st.error(f"❌ {message}")
    
    if st.button("✖️ Cancel", use_container_width=True):
        st.session_state['show_auth_form'] = False
        st.session_state['auth_source'] = None
        st.rerun()
    


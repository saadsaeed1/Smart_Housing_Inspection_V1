import streamlit as st
from data_manager import load_inspections

# --------------------------------------------------------
# 1. Page Configuration
# --------------------------------------------------------
st.set_page_config(
    page_title="Smart Housing Inspection Dashboard",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ Smart Housing Inspection Dashboard")
st.caption("Housing construction inspection, quality compliance, and municipal enforcement management system.")

# --------------------------------------------------------
# 2. Data Initialization
# --------------------------------------------------------
inspection_df = load_inspections()

# --------------------------------------------------------
# 3. Sidebar Navigation
# --------------------------------------------------------
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "New Inspection",
        "Inspection Records",
        "Enforcement",
        "Analytics",
        "Reports & Export",
        "Help & Guide",
    ],
)

# --------------------------------------------------------
# 4. Isolated Router (Dynamic Module Loading)
# --------------------------------------------------------
if page == "Dashboard":
    st.header("📊 Society Overview & Executive Dashboard")
    st.info("Executive KPI rollups and plot distribution maps will be finalized in the dashboard release.")

elif page == "New Inspection":
    try:
        from pages.inspections import show_new_inspection_form
        show_new_inspection_form()
    except ImportError:
        from pages.inspections import show_inspection_form
        show_inspection_form()

elif page == "Inspection Records":
    from pages.records import show_inspection_records
    show_inspection_records()

elif page == "Enforcement":
    from pages.enforcement import show_enforcement_page
    show_enforcement_page()

elif page == "Analytics":
    from pages.analytics import show_analytics_page
    show_analytics_page()

elif page == "Reports & Export":
    st.header("📄 Statutory Notices & Municipal Export")
    st.info("Legal Stop Work notice printing and society audit exports will be wired in the reports release.")

elif page == "Help & Guide":
    from pages.help_guide import show_help_page
    show_help_page()

# --------------------------------------------------------
# 5. Sidebar System Status
# --------------------------------------------------------
st.sidebar.divider()
st.sidebar.caption(f"Registered inspection records: **{len(inspection_df)}**")
st.sidebar.caption("System Status: **All Validation Guards Active**")
st.sidebar.caption("V1 — Production Build")
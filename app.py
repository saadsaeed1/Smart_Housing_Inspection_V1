
import streamlit as st
from data_manager import load_inspections
from pages.inspections import show_new_inspection_form


st.set_page_config(
    page_title="Smart Housing Inspection Dashboard",
    page_icon="🏗️",
    layout="wide",
)


st.title("🏗️ Smart Housing Inspection Dashboard")
st.write(
    "Housing construction inspection and compliance management system."
)


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
    ],
)


inspection_df = load_inspections()


if page == "Dashboard":

    st.header("Dashboard")
    st.info("Dashboard module will be developed in a later step.")


elif page == "New Inspection":

    show_new_inspection_form()


elif page == "Inspection Records":

    st.header("Inspection Records")
    st.info("Inspection Records module will be developed in a later step.")


elif page == "Enforcement":

    st.header("Enforcement")
    st.info("Enforcement module will be developed in a later step.")


elif page == "Analytics":

    st.header("Analytics")
    st.info("Analytics module will be developed in a later step.")


elif page == "Reports & Export":

    st.header("Reports & Export")
    st.info("Reports and Export module will be developed in a later step.")


st.sidebar.divider()

st.sidebar.caption(
    f"Current inspection records: {len(inspection_df)}"
)

st.sidebar.caption(
    "V1 — Development Build"
)

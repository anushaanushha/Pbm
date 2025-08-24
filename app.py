import streamlit as st

# App Configuration
st.set_page_config(page_title="PBM Optimization", page_icon="💊", layout="centered")

# Centered Title
st.markdown("<h1 style='text-align:center;'>PBM Optimization</h1>", unsafe_allow_html=True)
st.write("---")

# Dropdown for navigation
option = st.selectbox(
    "Select Option",
    [
        "Choose an option",
        "Real Time Formulary Impact Analysis",
        "Therapeutic Equivalence Optimization",
        "Drug Utilization Trend Prediction",
        "Cost Per Member Per Month Tracking"
    ]
)

if option == "Real Time Formulary Impact Analysis":
    st.switch_page("pages/formulatory.py")
elif option == "Therapeutic Equivalence Optimization":
    st.switch_page("pages/equivalence.py")
elif option == "Drug Utilization Trend Prediction":
    st.switch_page("pages/trendprediction.py")
elif option == "Cost Per Member Per Month Tracking":
    st.switch_page("pages/tracking.py")

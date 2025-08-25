import streamlit as st


st.set_page_config(page_title="PBM Optimization", page_icon="💊", layout="centered")




st.markdown("<h1 style='text-align:center;'>💊 PBM Optimization</h1>", unsafe_allow_html=True)
st.write("---")


option = st.selectbox(
    "Select Option",
    [
        "Choose an option",
        "Formulary Impact Analysis",
        "Therapeutic Equivalence Optimization",
        "Drug Utilization Trend Prediction",
        "Real Time Formulary Impact"
        
        
       
    ]
)

if option == "Formulary Impact Analysis":
    st.switch_page("pages/formulary.py")
elif option == "Therapeutic Equivalence Optimization":
    st.switch_page("pages/equivalence.py")
elif option == "Drug Utilization Trend Prediction":
    st.switch_page("pages/trendprediction.py")
elif option == "Real Time Formulary Impact":
    st.switch_page("pages/real_time.py")


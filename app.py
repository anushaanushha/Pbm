import streamlit as st
import base64

st.set_page_config(page_title="PBM Optimization", page_icon="💊", layout="centered")


def set_background(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: 100% auto;
        background-repeat: no-repeat;
        background-attachment: fixed;
        image-rendering: crisp-edges; 
    }}

    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}

    [data-testid="stToolbar"] {{
        right: 2rem;
    }}
    </style>
    """
    st.markdown(bg_img, unsafe_allow_html=True)


set_background("data/front.png")  


st.markdown("<h1 style='text-align:center; color:black;'>💊 PBM Optimization</h1>", unsafe_allow_html=True)
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
    st.switch_page("pages/real.py")


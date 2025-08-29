import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import base64


def set_background(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpeg;base64,{encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(bg_img, unsafe_allow_html=True)


set_background("data/back.jpeg")


model_path = "data/drug_trend3rd.pkl"
with open(model_path, "rb") as f:
    saved = pickle.load(f)

rf_model = saved["model"]
label_encoders = saved["encoders"]


data_path = "data/synthetic_drug_data_with_year_month.csv"
df = pd.read_csv(data_path)

st.title("Drug Cost Prediction & Trend Analysis")

option = st.selectbox(
    "Choose an option",
    ["Predict Future Trend", "Understand the Pattern","Seasonal Drug Sales Analysis"]
)


if option == "Predict Future Trend":
    drug_list = df["drugname"].unique().tolist()
    selected_drug = st.selectbox("Select Drug Name", drug_list)

   
    selected_year = st.slider("Select Year", 2025, 2030)

    
    selected_months = st.multiselect(
        "Select Month(s)", 
        options=list(range(1,13)), 
        default=list(range(1,13))
    )

    if not selected_months:
        st.warning("Please select at least one month.")
    else:
       
        drug_df = df[df["drugname"] == selected_drug]

        if not drug_df.empty:
            
            avg_values = {
                "season": drug_df["season"].mode()[0],
                "alternatedrug": drug_df["alternatedrug"].mode()[0],
                "alternatedrugcost": drug_df["alternatedrugcost"].mean(),
                "no_of_customer_using_drug": drug_df["no_of_customer_using_drug"].mode()[0],
                "no_of_customer_using_alternate_drug": drug_df["no_of_customer_using_alternate_drug"].mode()[0]
            }

            
            variation = 0.1  

            future_df = pd.DataFrame({
                "season": [avg_values["season"]] * len(selected_months),
                "drugname": [selected_drug] * len(selected_months),
                "alternatedrug": [avg_values["alternatedrug"]] * len(selected_months),
                "alternatedrugcost": [
                    np.round(avg_values["alternatedrugcost"] * np.random.uniform(1-variation, 1+variation), 2)
                    for _ in selected_months
                ],
                "no_of_customer_using_drug": [
                    int(avg_values["no_of_customer_using_drug"] * np.random.uniform(1-variation, 1+variation))
                    for _ in selected_months
                ],
                "no_of_customer_using_alternate_drug": [
                    int(avg_values["no_of_customer_using_alternate_drug"] * np.random.uniform(1-variation, 1+variation))
                    for _ in selected_months
                ],
                "Year": [selected_year] * len(selected_months),
                "Month": selected_months,
                "YearMonth": [f"{selected_year}-{m:02d}" for m in selected_months]  
            })



                    
           

           
            cat_cols = ["season", "drugname", "alternatedrug", "YearMonth"]
            for col in cat_cols:
                le = label_encoders[col]
                future_df[col] = future_df[col].apply(lambda x: x if x in le.classes_ else le.classes_[0])
                future_df[col] = le.transform(future_df[col])

            future_df["drugcost"] = rf_model.predict(future_df)

            
            st.subheader(f"Predicted Future Trend for {selected_drug} in {selected_year}")
            st.dataframe(future_df[[ "Month", "no_of_customer_using_drug", "drugcost", "drugname"]])



elif option == "Understand the Pattern":
    drug_list = df["drugname"].unique().tolist()
    selected_drug = st.selectbox("Select Drug Name", drug_list)
    selected_year = st.slider("Select Year", int(df["Year"].min()), int(df["Year"].max()))

    
    pattern_df = df[(df["drugname"] == selected_drug) & (df["Year"] == selected_year)]

    if not pattern_df.empty:
        pattern_df = pattern_df.sort_values("Month")

       
        fig, ax = plt.subplots(figsize=(10,6))
        ax.plot(pattern_df["Month"], pattern_df["drugcost"], marker='o', color='blue', label='Drug Cost')
        ax.plot(pattern_df["Month"], pattern_df["alternatedrugcost"], marker='o', color='red', label='Alternate Drug Cost')
        ax.set_xlabel("Month")
        ax.set_ylabel("Cost")
        ax.set_title(f"Cost Trend for {selected_drug} in {selected_year}")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
    else:

        st.warning("No data available for this drug and year.")
elif option == "Seasonal Drug Sales Analysis":
    st.title("💊 Seasonal Drug Sales Analysis")

    
    seasons = df["season"].unique()
    years = df["Year"].unique()

    selected_season = st.selectbox("Select Season", sorted(seasons))
    selected_years = st.multiselect("Select Year(s)", sorted(years), default=[years.min()])

   
    filtered_df = df[(df["season"] == selected_season) & (df["Year"].isin(selected_years))]

    if not filtered_df.empty:
        
        result = (
            filtered_df.groupby("drugname")
            .agg(
                total_customers=("no_of_customer_using_drug", "sum"),
                avg_cost=("drugcost", "mean")
            )
            .reset_index()
            .sort_values(by="total_customers", ascending=False)   
        )

        st.subheader(f"📌 Drugs Sold in {selected_season} for {', '.join(map(str, selected_years))}")
        st.dataframe(result)

        
        st.subheader("📊 Total Drug Usage (Combined Selected Years)")
        st.bar_chart(result.set_index("drugname")["total_customers"])

    else:
        st.warning("⚠️ No data available for the selected filters.")
    

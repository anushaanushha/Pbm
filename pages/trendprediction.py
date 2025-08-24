import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt

# -------------------------------
# Load trained model and encoders
# -------------------------------
model_path = "data/drug_trend3rd.pkl"
with open(model_path, "rb") as f:
    saved = pickle.load(f)

rf_model = saved["model"]
label_encoders = saved["encoders"]

# -------------------------------
# Load dataset
# -------------------------------
data_path = "data/train3.csv"
df = pd.read_csv(data_path)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("Drug Cost Prediction & Trend Analysis")

option = st.selectbox(
    "Choose an option",
    ["Predict Future Trend", "Understand the Pattern"]
)

# -------------------------------
# Predict Future Trend
# -------------------------------
# -------------------------------
# Predict Future Trend
# -------------------------------
if option == "Predict Future Trend":
    drug_list = df["drugname"].unique().tolist()
    selected_drug = st.selectbox("Select Drug Name", drug_list)

    # User selects Year
    selected_year = st.slider("Select Year", 2025, 2030)

    # User selects Month(s)
    selected_months = st.multiselect(
        "Select Month(s)", 
        options=list(range(1,13)), 
        default=list(range(1,13))
    )

    if not selected_months:
        st.warning("Please select at least one month.")
    else:
        # Filter historical data for this drug
        drug_df = df[df["drugname"] == selected_drug]

        if not drug_df.empty:
            # Prepare future data for selected months
            future_df = pd.DataFrame({
                "season": np.random.choice(drug_df["season"].unique(), size=len(selected_months)),
                "drugname": selected_drug,
                "alternatedrug": np.random.choice(drug_df["alternatedrug"].unique(), size=len(selected_months)),
                "alternatedrugcost": np.random.choice(drug_df["alternatedrugcost"], size=len(selected_months)),
                "no_of_customer_using_drug": np.random.choice(drug_df["no_of_customer_using_drug"], size=len(selected_months)),
                "no_of_customer_using_alternate_drug": np.random.choice(drug_df["no_of_customer_using_alternate_drug"], size=len(selected_months)),
                "Year": selected_year,
                "Month": selected_months,
                "YearMonth": [f"{selected_year}-{m:02d}" for m in selected_months]  # store as string YYYY-MM
            })

            # Encode categorical columns safely
            cat_cols = ["season", "drugname", "alternatedrug", "YearMonth"]
            for col in cat_cols:
                le = label_encoders[col]
                future_df[col] = future_df[col].apply(lambda x: x if x in le.classes_ else le.classes_[0])
                future_df[col] = le.transform(future_df[col])

            # Predict drugcost
            future_df["drugcost"] = rf_model.predict(future_df)

            # Display relevant columns
            st.subheader(f"Predicted Future Trend for {selected_drug} in {selected_year}")
            st.dataframe(future_df[[ "Month", "no_of_customer_using_drug", "drugcost", "drugname"]])


# -------------------------------
# Understand the Pattern
# -------------------------------
elif option == "Understand the Pattern":
    drug_list = df["drugname"].unique().tolist()
    selected_drug = st.selectbox("Select Drug Name", drug_list)
    selected_year = st.slider("Select Year", int(df["Year"].min()), int(df["Year"].max()))

    # Filter data for selected drug and year
    pattern_df = df[(df["drugname"] == selected_drug) & (df["Year"] == selected_year)]

    if not pattern_df.empty:
        pattern_df = pattern_df.sort_values("Month")

        # Plot line chart
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
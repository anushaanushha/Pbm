import streamlit as st
import pandas as pd
import base64

# -----------------------
# Background setup
# -----------------------
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

# -----------------------
# Load data
# -----------------------
@st.cache_data
def load_data():
    return pd.read_csv("data/full_dataset_with_new_avg_cost_and_score.csv")

df = load_data()

# -----------------------
# App UI
# -----------------------
st.title("💊 Formulary Impact Analysis")

drug_list = sorted(df['Medicine'].dropna().unique().tolist())
selected_drugs = st.multiselect("Select Drug(s):", drug_list)

if selected_drugs:
    selected_data = df[df['Medicine'].isin(selected_drugs)]
    total_base_cost = selected_data['Drug_Cost'].sum()

    st.subheader("📌 Base Drug Costs (USD)")
    st.write(selected_data[['Medicine', 'Drug_Cost']])

    st.subheader("🛡 Insurance Option")
    use_insurance = st.checkbox("Apply Insurance Discount")

    # -----------------------
    # Insurance Discount Cost
    # -----------------------
    insurance_cost = None
    if use_insurance:
        insured_data = selected_data[['Medicine', 'Drug_Cost', 'Insurance_Drug', 'Insurance_Saving_%', 'Insurance_Drug_FinalCost']].copy()
        insurance_cost = insured_data['Insurance_Drug_FinalCost'].sum()
        st.write("### Insurance Cost Details")
        st.write(insured_data)

    # -----------------------
    # Cheaper Alternatives
    # -----------------------
    alt_cost = None
    alt_suggestions = []
    for _, row in selected_data.iterrows():
        base_drug = row['Medicine']
        base_cost = row['Drug_Cost']
        alt_costs = [(row.get(f'Alternative {i}'), row.get(f'Cost {i}'))
                     for i in range(1, 6)
                     if pd.notna(row.get(f'Alternative {i}')) and pd.notna(row.get(f'Cost {i}'))]

        if alt_costs:
            cheapest_alt = min(alt_costs, key=lambda x: x[1])
            if cheapest_alt[1] < base_cost:
                alt_suggestions.append([base_drug, base_cost, cheapest_alt[0], cheapest_alt[1]])

    if alt_suggestions:
        alt_df = pd.DataFrame(alt_suggestions, columns=["Base Drug", "Base Cost (USD)", "Cheapest Alternative", "Alternative Cost (USD)"])
        alt_cost = alt_df['Alternative Cost (USD)'].sum()
        st.subheader("🔄 Suggested Cheaper Alternatives (USD)")
        st.write(alt_df)

    # -----------------------
    # Final Comparison
    # -----------------------
    if insurance_cost is None and alt_cost is None:
        st.info("No insurance discount or cheaper alternatives available.")
    else:
        options = {
            "Insurance": insurance_cost if insurance_cost else float('inf'),
            "Alternative": alt_cost if alt_cost else float('inf')
        }
        best_option = min(options, key=options.get)
        best_cost = options[best_option]
        total_savings = total_base_cost - best_cost

        st.subheader("💡 Final Cost Analysis")
        st.success(f"💰 *Total Base Cost:* ${total_base_cost:,.2f}")
        st.success(f"💸 *Total Final Cost ({best_option}):* ${best_cost:,.2f}")
        st.success(f"🎉 *Total Savings with {best_option}:* ${total_savings:,.2f}")

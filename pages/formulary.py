import streamlit as st
import pandas as pd

# Load dataset
@st.cache_data
def load_data():
    return pd.read_csv("data/updated_prescription_dates.csv")

df = load_data()

st.title("💊 Formulary Impact Analysis")

# Multi-select dropdown for drugs
drug_list = sorted(df['Medicine'].dropna().unique().tolist())
selected_drugs = st.multiselect("Select Drug(s):", drug_list)

if selected_drugs:
    # Filter selected drugs
    selected_data = df[df['Medicine'].isin(selected_drugs)]

    # Base cost calculation
    st.subheader("📌 Base Drug Costs (USD)")
    total_base_cost = selected_data['Drug_Cost'].sum()
    st.write(selected_data[['Medicine', 'Drug_Cost']])

    # Insurance toggle
    st.subheader("🛡 Insurance Option")
    use_insurance = st.checkbox("Apply Insurance Discount")

    if use_insurance:
        # Insurance applied
        insured_data = selected_data[['Medicine', 'Drug_Cost', 'Insurance_Drug', 'Insurance_Saving_%', 'Insurance_Drug_FinalCost']].copy()
        total_final_cost = insured_data['Insurance_Drug_FinalCost'].sum()
        savings = total_base_cost - total_final_cost

        st.write("### Cost Summary with Insurance (USD)")
        st.write(insured_data)

        st.success(f"💰 **Total Base Cost:** ${total_base_cost:,.2f}")
        st.success(f"💸 **Total Final Cost (With Insurance):** ${total_final_cost:,.2f}")
        st.success(f"🎉 **Total Savings:** ${savings:,.2f}")

    else:
        # No insurance — find the cheapest alternative per base drug
        st.subheader("🔄 Suggested Cheaper Alternatives (USD)")
        alt_suggestions = []

        for _, row in selected_data.iterrows():
            base_drug = row['Medicine']
            base_cost = row['Drug_Cost']
            alt_costs = []

            for i in range(1, 6):
                alt_name = row.get(f'Alternative {i}')
                alt_price = row.get(f'Cost {i}')
                if pd.notna(alt_name) and pd.notna(alt_price):
                    alt_costs.append((alt_name, alt_price))

            if alt_costs:
                # Sort to get cheapest
                cheapest_alt = sorted(alt_costs, key=lambda x: x[1])[0]
                if cheapest_alt[1] < base_cost:
                    alt_suggestions.append([base_drug, base_cost, cheapest_alt[0], cheapest_alt[1]])

        if alt_suggestions:
            alt_df = pd.DataFrame(alt_suggestions, columns=["Base Drug", "Base Cost (USD)", "Cheapest Alternative", "Alternative Cost (USD)"])
            st.write(alt_df)

            total_alt_cost = alt_df['Alternative Cost (USD)'].sum()
            savings = total_base_cost - total_alt_cost

            st.success(f"💰 **Total Base Cost:** ${total_base_cost:,.2f}")
            st.success(f"💸 **Total Cost with Alternatives:** ${total_alt_cost:,.2f}")
            st.success(f"🎉 **You Could Save:** ${savings:,.2f}")
        else:
            st.info("No cheaper alternatives available for the selected drugs.")

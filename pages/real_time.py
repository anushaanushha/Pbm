import streamlit as st
import sqlite3
import os
import pandas as pd
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

# Call function
set_background("data/back.jpg")


DB_FILE = "data/formulary.db"


conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_medicine ON formulary(Medicine)")
    conn.commit()
except Exception as e:
    st.warning(f"Index creation issue: {e}")


def get_drug_info(medicine_name):
    cursor.execute("SELECT * FROM formulary WHERE Medicine = ?", (medicine_name,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]

    if row:
        
        data = dict(zip(columns, row))
        cost_cols = ["Drug_Cost", "Cost1", "Cost2", "Cost3", "Cost4", "Cost5"]
        alt_cols = ["Medicine", "Alternative_1", "Alternative_2", "Alternative_3", "Alternative_4", "Alternative_5"]

       
        costs = [data.get(c) for c in cost_cols if data.get(c) not in (None, 0)]
        cheapest_cost = min(costs)

        
        cheapest_drug = "Original"
        for i, c in enumerate(cost_cols):
            if data.get(c) == cheapest_cost:
                if i == 0:
                    cheapest_drug = data["Medicine"]
                else:
                    cheapest_drug = data.get(f"Alternative_{i}") or f"Alternative_{i}"
                break

        saving_percent = round((data["Drug_Cost"] - cheapest_cost) * 100 / data["Drug_Cost"], 2)
        effective_cost = min(cheapest_cost, data.get("Insurance_Drug_FinalCost") or float('inf'))

        return {
            "Exists": True,
            "Medicine": data["Medicine"],
            "Drug_Cost": data["Drug_Cost"],
            "Cheapest_Option": cheapest_drug,
            "Cheapest_Cost": cheapest_cost,
            "Saving_vs_Original_%": saving_percent,
            "Insurance_Drug": data.get("Insurance_Drug"),
            "Insurance_Drug_FinalCost": data.get("Insurance_Drug_FinalCost"),
            "Effective_Cost": effective_cost
        }
    else:
        
        return {
            "Exists": False,
            "Medicine": medicine_name,
            "Drug_Cost": None,
            "Cheapest_Option": medicine_name,
            "Cheapest_Cost": None,
            "Saving_vs_Original_%": 0,
            "Insurance_Drug": None,
            "Insurance_Drug_FinalCost": None,
            "Effective_Cost": None
        }


st.title("💊 Real-Time Formulary Impact Dashboard")

st.markdown("Enter a medicine name to see its cost and best alternative:")

medicine_name = st.text_input("Medicine Name")

if medicine_name:
    info = get_drug_info(medicine_name.strip())

    if info["Exists"]:
        st.success(f"💡 Medicine exists in database! Best alternative: {info['Cheapest_Option']}")
    else:
        st.info("⚠️ Medicine is new. No alternative exists; use the same drug.")

    st.subheader("Drug Cost & Savings Info")
    st.table(pd.DataFrame([info]))

with st.expander("➕ Add New Drug Record (Optional)"):
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False

    with st.form("new_entry"):
        record = {
            "id": st.text_input("ID", key="id_input"),
            "Medicine": st.text_input("Medicine", key="med_input"),
            "Drug_Cost": st.number_input("Drug Cost", min_value=0.0, step=0.01, key="cost_input"),
            "Alternative_1": st.text_input("Alternative 1 (optional)", key="alt1_input"),
            "Alternative_2": st.text_input("Alternative 2 (optional)", key="alt2_input"),
            "Alternative_3": st.text_input("Alternative 3 (optional)", key="alt3_input"),
            "Alternative_4": st.text_input("Alternative 4 (optional)", key="alt4_input"),
            "Alternative_5": st.text_input("Alternative 5 (optional)", key="alt5_input"),
            "Cost1": st.number_input("Cost1 (optional)", min_value=0.0, step=0.01, value=0.0, key="c1_input"),
            "Cost2": st.number_input("Cost2 (optional)", min_value=0.0, step=0.01, value=0.0, key="c2_input"),
            "Cost3": st.number_input("Cost3 (optional)", min_value=0.0, step=0.01, value=0.0, key="c3_input"),
            "Cost4": st.number_input("Cost4 (optional)", min_value=0.0, step=0.01, value=0.0, key="c4_input"),
            "Cost5": st.number_input("Cost5 (optional)", min_value=0.0, step=0.01, value=0.0, key="c5_input"),
            "Insurance_Drug": st.text_input("Insurance Drug (optional)", key="ins_input"),
            "Insurance_Drug_FinalCost": st.number_input(
                "Insurance Drug Final Cost (optional)", min_value=0.0, step=0.01, value=0.0, key="ins_cost_input"
            )
        }

        submitted = st.form_submit_button("Insert")

        if submitted:
            st.session_state.form_submitted = True
            medicine_name = record["Medicine"].strip()

            
            for key in record:
                if record[key] == "" or record[key] is None:
                    record[key] = None
            for i in range(1, 6):
                record[f"Alternative_{i}"] = record.get(f"Alternative_{i}") or None
                record[f"Cost{i}"] = record.get(f"Cost{i}") or None

            with sqlite3.connect(DB_FILE, timeout=30) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM formulary WHERE Medicine = ?", (medicine_name,))
                row = cursor.fetchone()
                columns = [desc[0] for desc in cursor.description] if row else None

                if row:
                    st.warning(f"⚠️ Medicine '{medicine_name}' already exists in the database!")
                else:
                    columns_sql = ", ".join([f'"{col}"' for col in record.keys()])
                    placeholders = ", ".join(["?"] * len(record))
                    sql = f"INSERT INTO formulary ({columns_sql}) VALUES ({placeholders})"
                    cursor.execute(sql, list(record.values()))
                    conn.commit()

                    st.success(f"✅ New medicine '{medicine_name}' inserted successfully!")

                    
                    try:
                        clear_keys = [
                            "id_input", "med_input", "cost_input",
                            "alt1_input", "alt2_input", "alt3_input", "alt4_input", "alt5_input",
                            "c1_input", "c2_input", "c3_input", "c4_input", "c5_input",
                            "ins_input", "ins_cost_input"
                        ]

                        for k in clear_keys:
                            if k in ["cost_input", "c1_input", "c2_input", "c3_input", "c4_input", "c5_input", "ins_cost_input"]:
                                st.session_state[k] = 0.0
                            else:
                                st.session_state[k] = ""

                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f" ")
                    

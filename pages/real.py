import streamlit as st
import sqlite3
import pandas as pd
import base64

DB_FILE = "data/formulary.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

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

# ---------- Helper Functions ----------
def calculate_effective_cost(row):
    costs = []
    if row["Drug_Cost"] and row["Drug_Cost"] > 0:
        costs.append(row["Drug_Cost"])
    if row.get("Insurance_Drug_FinalCost") and row["Insurance_Drug_FinalCost"] > 0:
        costs.append(row["Insurance_Drug_FinalCost"])
    return min(costs) if costs else None

def find_best_alternative(use, therapeutic_class):
    cursor.execute(
        "SELECT * FROM formulary WHERE use=? AND TherapeuticClass=?",
        (use, therapeutic_class)
    )
    rows = cursor.fetchall()
    if not rows:
        return None, None

    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    df["Effective_Cost"] = df.apply(calculate_effective_cost, axis=1)
    cheapest_row = df.loc[df["Effective_Cost"].idxmin()]

    cheapest_drug = (
        cheapest_row["Medicine"]
        if cheapest_row["Effective_Cost"] == cheapest_row["Drug_Cost"]
        else cheapest_row.get("Insurance_Drug")
    )
    return cheapest_drug, cheapest_row["Effective_Cost"]
def get_best_alternative_info(medicine_name):
    med = medicine_name.strip().lower()
    cursor.execute("SELECT * FROM formulary WHERE lower(Medicine)=?", (med,))
    row = cursor.fetchone()
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description]
    record = dict(zip(columns, row))
    best_alt, best_cost = None, None
    if record.get("Alternative_1") and record.get("Cost1"):
        best_alt = record["Alternative_1"]
        best_cost = record["Cost1"]
    return {
        "Medicine": record["Medicine"],
        "Drug_Cost": record["Drug_Cost"],
        "Use": record["use"] if "use" in record else record.get("Use"),
        "TherapeuticClass": record["TherapeuticClass"],
        "Best_Alternative": best_alt,
        "Best_Alternative_Cost": best_cost
    }

def insert_new_drug(medicine, cost, use, thera_class):
    cursor.execute("SELECT * FROM formulary WHERE Medicine=?", (medicine,))
    if cursor.fetchone():
        return False, None, None  

    # Find best alternative before inserting
    alt_drug, alt_cost = find_best_alternative(use, thera_class)

    cursor.execute(
        """
        INSERT INTO formulary (
            Medicine, Drug_Cost, use, TherapeuticClass,
            Alternative_1, Cost1,
            Alternative_2, Alternative_3, Alternative_4, Alternative_5,
            sideEffect0, sideEffect1, sideEffect2, sideEffect3,
            Cost2, Cost3, Cost4, Cost5,
            insurance, Insurance_Drug, Insurance_Saving_Percent, Insurance_Drug_FinalCost
        )
        VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL,
                NULL, NULL, NULL, NULL,
                NULL, NULL, NULL, NULL,
                NULL, NULL, NULL, NULL)
        """,
        (medicine, cost, use, thera_class, alt_drug, alt_cost)
    )
    conn.commit()
    return True, alt_drug, alt_cost

def get_drug_info(medicine_name):
    med = medicine_name.strip().lower()
    cursor.execute("SELECT * FROM formulary WHERE lower(Medicine)=?", (med,))
    row = cursor.fetchone()
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


st.title("💊 Real-Time Formulary Impact Dashboard")

if "results" not in st.session_state:
    st.session_state.results = []


with st.form("drug_entry", clear_on_submit=True):
    medicine_name = st.text_input("🔍 Enter Medicine Name")
    submitted = st.form_submit_button("Check Medicine")

    if submitted and medicine_name:
        info = get_drug_info(medicine_name.strip())
        if info:
            st.session_state.results.append(info)
        else:
            st.warning(f"⚠ Medicine '{medicine_name}' not found in DB. Add it below.")

if st.session_state.results:
    st.subheader("📊 Checked Medicines")
    display_df = pd.DataFrame([
        get_best_alternative_info(r["Medicine"]) for r in st.session_state.results
    ])
    st.dataframe(display_df)


st.subheader("➕ Add a New Drug to Database")
with st.form("add_new_drug", clear_on_submit=True):
    new_med = st.text_input("Medicine Name")
    new_cost = st.number_input("Drug Cost", min_value=0.0, step=0.01)
    new_use = st.text_input("Use")
    new_class = st.text_input("Therapeutic Class")
    add_btn = st.form_submit_button("Insert Drug")

    if add_btn and new_med:
        success, alt_drug, alt_cost = insert_new_drug(
            new_med.strip(), new_cost, new_use.strip(), new_class.strip()
        )
        if success:
            if alt_drug:
                st.success(
                    f"✅ '{new_med}' added! Best alternative stored: {alt_drug} (Cost {alt_cost})"
                )
            else:
                st.success(
                    f"✅ '{new_med}' added! ⚠ No alternative found for this class."
                )
        else:
            st.warning(f"⚠ Medicine '{new_med}' already exists in DB.")

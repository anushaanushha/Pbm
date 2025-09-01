import streamlit as st
import sqlite3
import os
import pandas as pd
import base64

# ========== Background Setup ==========
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

# ========== Database Setup ==========
DB_FILE = "data/formulary.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS formulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Medicine TEXT,
    Drug_Cost REAL,
    use TEXT,
    TherapeuticClass TEXT
)
""")
conn.commit()

# Index for faster lookup
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_medicine ON formulary(Medicine)")
    conn.commit()
except Exception as e:
    st.warning(f"Index creation issue: {e}")

# ========== Functions ==========
def get_drug_info(medicine_name):
    """Fetch drug info and find cheapest alternatives (top 5)"""
    cursor.execute("SELECT * FROM formulary WHERE Medicine = ?", (medicine_name,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]

    if row:
        data = dict(zip(columns, row))

        # Find alternatives (same Use + Therapeutic Class, exclude self)
        cursor.execute("""
            SELECT Medicine, Drug_Cost FROM formulary
            WHERE use = ? AND TherapeuticClass = ? AND Medicine != ?
            ORDER BY Drug_Cost ASC
            LIMIT 5
        """, (data["use"], data["TherapeuticClass"], data["Medicine"]))
        alternatives = cursor.fetchall()

        if alternatives:
            alt_df = pd.DataFrame(alternatives, columns=["Alternative", "Alt_Cost"])
            cheapest = alt_df.loc[alt_df["Alt_Cost"].idxmin()]
            cheapest_drug = cheapest["Alternative"]
            cheapest_cost = cheapest["Alt_Cost"]
            saving_percent = round((data["Drug_Cost"] - cheapest_cost) * 100 / data["Drug_Cost"], 2)
        else:
            cheapest_drug = data["Medicine"]
            cheapest_cost = data["Drug_Cost"]
            saving_percent = 0

        return {
            "Exists": True,
            "Medicine": data["Medicine"],
            "Use": data["use"],
            "TherapeuticClass": data["TherapeuticClass"],
            "Drug_Cost": data["Drug_Cost"],
            "Cheapest_Option": cheapest_drug,
            "Cheapest_Cost": cheapest_cost,
            "Saving_vs_Original_%": saving_percent
        }, alternatives
    else:
        return {
            "Exists": False,
            "Medicine": medicine_name,
            "Drug_Cost": None,
            "Cheapest_Option": medicine_name,
            "Cheapest_Cost": None,
            "Saving_vs_Original_%": 0
        }, []


st.title("💊 Real-Time Formulary Impact Dashboard")
st.markdown("Enter a medicine name to see its cost and best alternative:")

medicine_name = st.text_input("Medicine Name")

if medicine_name:
    info, alternatives = get_drug_info(medicine_name.strip())

    if info["Exists"]:
        st.success(f"💡 Medicine exists in database! Best alternative: {info['Cheapest_Option']}")
    else:
        st.info("⚠️ Medicine is new. No alternative exists yet.")

    st.subheader("📊 Drug Cost & Savings Info")
    st.table(pd.DataFrame([info]))

    if alternatives:
        st.subheader("🔄 Top 5 Alternatives")
        st.dataframe(pd.DataFrame(alternatives, columns=["Alternative", "Alt_Cost"]))


with st.expander("➕ Add New Drug Record"):
    with st.form("new_entry"):
        record = {
            "Medicine": st.text_input("Medicine"),
            "Drug_Cost": st.number_input("Drug Cost", min_value=0.0, step=0.01),
            "use": st.text_input("Use (e.g., Allergy, Fever, Pain)"),
            "TherapeuticClass": st.text_input("Therapeutic Class (e.g., Antihistamine, Analgesic)")
        }

        submitted = st.form_submit_button("Insert")

        if submitted:
            med_name = record["Medicine"].strip()
            if med_name:
                cursor.execute("SELECT * FROM formulary WHERE Medicine = ?", (med_name,))
                row = cursor.fetchone()

                if row:
                    st.warning(f"⚠️ Medicine '{med_name}' already exists in the database!")
                else:
                    columns_sql = ", ".join(record.keys())
                    placeholders = ", ".join(["?"] * len(record))
                    sql = f"INSERT INTO formulary ({columns_sql}) VALUES ({placeholders})"
                    cursor.execute(sql, list(record.values()))
                    conn.commit()
                    st.success(f"✅ New medicine '{med_name}' inserted successfully!")
            else:
                st.error("⚠️ Medicine name cannot be empty.")

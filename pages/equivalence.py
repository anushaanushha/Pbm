import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import streamlit as st

# -----------------------------
# Helpers
# -----------------------------
def parse_cost(x):
    s = str(x).strip()
    cleaned = re.sub(r"[^0-9.]", "", s)
    if cleaned.count(".") > 1 or cleaned == "":
        return float("inf")
    try:
        return float(cleaned)
    except:
        return float("inf")

def row_alternatives(row):
    alts, costs = [], []
    for j in range(1, 6):
        a_col, c_col = f"Alternative {j}", f"Cost {j}"
        if a_col in row and c_col in row:
            alt = str(row[a_col]).strip()
            cost = parse_cost(row[c_col])
            if alt and alt.upper() != "NULL" and cost != float("inf"):
                alts.append(alt)
                costs.append(cost)
    pairs = list(zip(alts, costs))
    pairs.sort(key=lambda x: x[1])
    return pairs

# -----------------------------
# Load dataset
# -----------------------------
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df.fillna("NULL", inplace=True)
    return df

file_path = "data/updated_prescription_dates.csv"   # keep your file in same folder
df = load_data(file_path)

# -----------------------------
# Prepare TF-IDF & KNN model
# -----------------------------
df["combined"] = (
    df["Medicine"].astype(str) + " "
    + (df["Therapeutic Class"].astype(str) if "Therapeutic Class" in df.columns else "")
    + " "
    + (df["use"].astype(str) if "use" in df.columns else "")
)

tfidf = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf.fit_transform(df["combined"])

knn = NearestNeighbors(n_neighbors=6, metric="cosine")
knn.fit(tfidf_matrix)

# -----------------------------
# Recommendation Function
# -----------------------------
def recommend_and_format(medicine_name: str):
    matches = df[df["Medicine"].str.lower() == medicine_name.lower()]
    if matches.empty:
        return f"⚠️ Medicine '{medicine_name}' not found in database."

    idx = matches.index[0]
    input_row = df.loc[idx]

    # 1) Cheapest from the INPUT medicine's own row
    input_alts = row_alternatives(input_row)
    top_line = None
    if input_alts:
        cheapest_from_input = input_alts[0]
        top_line = {
            "alt": cheapest_from_input[0],
            "cost": cheapest_from_input[1],
            "from_med": input_row["Medicine"],
            "from_cost": parse_cost(input_row["Drug_Cost"]) if "Drug_Cost" in df.columns else "NA",
        }

    # 2) Collect cheapest-from-each similar medicine
    distances, indices = knn.kneighbors(tfidf_matrix[idx], n_neighbors=6)
    others = []
    for i in indices.flatten():
        if i == idx:
            continue
        row_i = df.iloc[i]
        pairs = row_alternatives(row_i)
        if not pairs:
            continue
        cheapest_i = pairs[0]
        others.append({
            "alt": cheapest_i[0],
            "cost": cheapest_i[1],
            "from_med": row_i["Medicine"],
            "from_cost": parse_cost(row_i["Drug_Cost"]) if "Drug_Cost" in df.columns else "NA",
        })

    # Deduplicate
    seen = {}
    def keyfn(x): return x["alt"].strip().lower()
    for item in others:
        k = keyfn(item)
        if k not in seen or item["cost"] < seen[k]["cost"]:
            seen[k] = item
    others = list(seen.values())
    others.sort(key=lambda x: x["cost"])

    if top_line is None:
        if not others:
            return f"❌ No alternatives found for '{medicine_name}'."
        top_line = others[0]
        others = others[1:]

    others = [o for o in others if keyfn(o) != keyfn(top_line)]

    # --- Pretty formatting ---
    lines = []
    lines.append(f"👉 **Drug name**: {top_line['from_med']}")
    lines.append(f"**Original Cost**: {top_line['from_cost']}")
    lines.append(f"💰 **Cheapest Alternative Drug**: {top_line['alt']}")
    lines.append(f"**Cost**: :green[{top_line['cost']}]")  # highlight cost in green

    return "<br>".join(lines)   # Use <br> for line breaks

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("💊 Medicine Alternative Finder")
st.write("Search for a medicine and get the cheapest alternative recommendations.")

# Medicine dropdown (auto-suggest)
medicine_list = sorted(df["Medicine"].unique())
medicine_input = st.selectbox("🔎 Select or type a medicine name:", medicine_list)

if medicine_input:
    result = recommend_and_format(medicine_input)
    st.markdown(result, unsafe_allow_html=True)   # Allow HTML for <br> line breaks
else:
    st.warning("Please select or type a medicine name.")

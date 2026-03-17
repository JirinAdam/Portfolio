import re
import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(".")

KEYWORDS_CSV = BASE_DIR / "cleaned_keywords.csv"
DB_PATH = BASE_DIR / "job_database.db"
GROUPS_CSV = BASE_DIR / "keywords_grouped_Var.csv"

OUT_CSV = BASE_DIR / "keyword_count.csv"

# -----------------------------
# 1) Load keywords
# -----------------------------
kw_df = pd.read_csv(KEYWORDS_CSV)
if "keyword" not in kw_df.columns:
    raise ValueError("cleaned_keywords.csv must contain column 'keyword'")

raw_keywords = (
    kw_df["keyword"]
    .dropna()
    .astype(str)
    .map(str.strip)
)

# Dedupe case-insensitive, keep first original
seen = set()
kw_list = []
for k in raw_keywords:
    lk = k.lower()
    if lk and lk not in seen:
        seen.add(lk)
        kw_list.append(k)

print(f"Keywords loaded: {len(kw_list)}")

# -----------------------------
# 2) Load keyword -> group mapping (case-insensitive)
# -----------------------------


print(f"Checking file: {GROUPS_CSV}")
print(f"File exists: {GROUPS_CSV.exists()}")
if GROUPS_CSV.exists():
    print(f"File size: {GROUPS_CSV.stat().st_size} bytes")
    # načti prvních pár řádků pro debug
    with open(GROUPS_CSV, 'r', encoding='utf-8') as f:
        print("First 3 lines:")
        for i, line in enumerate(f):
            if i < 3:
                print(f"  {i}: {repr(line)}")
            else:
                break

grp_df = pd.read_csv(GROUPS_CSV, sep=None, engine='python')  # auto-detect separator
print(f"Columns in CSV: {list(grp_df.columns)}")
print(f"Shape: {grp_df.shape}")

if not {"keyword", "group"}.issubset(set(grp_df.columns)):
    raise ValueError("Groups CSV must contain columns: 'keyword' and 'group'")

grp_df["keyword_norm"] = grp_df["keyword"].astype(str).str.strip().str.lower()
grp_df["group_norm"] = grp_df["group"].astype(str).str.strip()

group_map = dict(zip(grp_df["keyword_norm"], grp_df["group_norm"]))
print(f"Groups loaded: {len(group_map)} mappings")

# -----------------------------
# 3) Split keywords into token-safe vs regex-needed
# -----------------------------
token_keywords = []
regex_keywords = []
for kw in kw_list:
    k = kw.strip()
    if re.fullmatch(r"[A-Za-z0-9]+", k):
        token_keywords.append(k)
    else:
        regex_keywords.append(k)

print(f"Token keywords: {len(token_keywords)}")
print(f"Regex keywords: {len(regex_keywords)}")

# -----------------------------
# 4) Load job_offers columns
# -----------------------------
con = sqlite3.connect(DB_PATH)
try:
    offers = pd.read_sql_query(
        "SELECT technologies_os, technologies_optional FROM job_offers",
        con
    )
finally:
    con.close()

print(f"Job offers loaded: {len(offers)} rows")

t_os = offers["technologies_os"].fillna("").astype(str)
t_opt = offers["technologies_optional"].fillna("").astype(str)
row_texts = (t_os + " " + t_opt).str.lower().tolist()

# -----------------------------
# 5) Tokenize rows once (for token keywords)
# -----------------------------
row_token_sets = []
for text in tqdm(row_texts, desc="Tokenizing rows"):
    row_token_sets.append(set(re.findall(r"[a-z0-9]+", text)))

# -----------------------------
# 6) Count occurrences
# -----------------------------
results_count = {}

# token keywords
for kw in tqdm(token_keywords, desc="Counting token-keywords"):
    k = kw.lower()
    cnt = sum(1 for s in row_token_sets if k in s)
    results_count[kw] = cnt

# regex keywords
def compile_symbol_keyword_regex(keyword: str) -> re.Pattern:
    k = keyword.lower()
    pattern = r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])"
    return re.compile(pattern)

compiled = [(kw, compile_symbol_keyword_regex(kw)) for kw in regex_keywords]
for kw, rx in tqdm(compiled, desc="Counting regex-keywords"):
    cnt = sum(1 for txt in row_texts if rx.search(txt) is not None)
    results_count[kw] = cnt

# -----------------------------
# 7) Build final output with group
# -----------------------------
rows = []
for kw in kw_list:
    kw_norm = kw.strip().lower()
    group = group_map.get(kw_norm, "Unmapped")
    rows.append({
        "keyword": kw,
        "count": int(results_count.get(kw, 0)),
        "group": group
    })

out_df = pd.DataFrame(rows).sort_values(["count", "keyword"], ascending=[False, True])
out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")

print(f"Saved: {OUT_CSV.resolve()}")
print("Sanity check:")
for ex in [".NET", "C++", "C#", "SQL", "Git"]:
    ex_norm = ex.lower()
    ex_group = group_map.get(ex_norm, "Unmapped")
    ex_count = out_df.loc[out_df["keyword"].str.lower() == ex_norm, "count"]
    ex_count = int(ex_count.iloc[0]) if len(ex_count) else None
    print(f"  {ex}: count={ex_count}, group={ex_group}")
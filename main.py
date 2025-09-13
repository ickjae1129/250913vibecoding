import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO
from pathlib import Path

st.set_page_config(page_title="MBTI Top 10 Countries", layout="wide")
st.title("MBTI 유형별 비율이 가장 높은 국가 Top 10")
st.caption("기본 데이터 또는 CSV 업로드 → MBTI 유형 선택 → 인터랙티브 막대 그래프")

# --- Sidebar help ---
st.sidebar.header("설정")
st.sidebar.markdown(
    """
    **사용 방법**
    1) 기본적으로 동일 폴더의 `countriesMBTI_16types.csv` 데이터를 사용합니다.
    2) 만약 해당 파일이 없거나 다른 데이터를 사용하고 싶으면 CSV를 업로드하세요.
    3) MBTI 유형을 선택하면, 해당 유형 비율이 높은 국가 Top 10이 표시됩니다.
    """
)

# --- Helpers ---
MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

POSSIBLE_COUNTRY_COLS = ["country", "nation", "location", "region", "국가", "나라", "지역"]


def detect_country_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        lc = str(c).strip().lower()
        if lc in POSSIBLE_COUNTRY_COLS or "country" in lc or "국가" in c or "나라" in c:
            return c
    return df.columns[0]


def pick_mbti_cols(df: pd.DataFrame) -> list:
    cols_upper = {c.upper(): c for c in df.columns}
    return [cols_upper[t] for t in MBTI_TYPES if t in cols_upper]


def to_numeric(df: pd.DataFrame, exclude: list) -> pd.DataFrame:
    num = df.copy()
    for c in num.columns:
        if c not in exclude:
            num[c] = pd.to_numeric(num[c], errors="coerce")
    return num


def infer_to_proportion(df_num: pd.DataFrame, type_cols: list) -> pd.DataFrame:
    sums = df_num[type_cols].sum(axis=1)
    out = df_num.copy()
    out[type_cols] = out[type_cols].div(sums.replace(0, pd.NA), axis=0)
    return out, sums

# --- Load default data or fallback to upload ---
def_path = Path("countriesMBTI_16types.csv")
if def_path.exists():
    st.info("기본 데이터(countriesMBTI_16types.csv)를 사용합니다.")
    df = pd.read_csv(def_path)
else:
    upload = st.file_uploader("CSV 파일 업로드", type=["csv"])
    if upload is None:
        st.warning("CSV를 업로드하거나 기본 데이터를 같은 폴더에 두세요.")
        st.stop()
    raw_bytes = upload.read()
    for enc in ("utf-8", "cp932", "euc-kr", "latin1"):
        try:
            df = pd.read_csv(StringIO(raw_bytes.decode(enc)))
            break
        except Exception:
            df = None
    if df is None:
        st.error("CSV를 읽는 데 실패했습니다.")
        st.stop()

st.subheader("데이터 미리보기")
st.dataframe(df.head(50), use_container_width=True)

country_col = detect_country_col(df)
mbti_cols = pick_mbti_cols(df)
if len(mbti_cols) == 0:
    st.error("MBTI 열을 찾지 못했습니다.")
    st.stop()

num_df = to_numeric(df, exclude=[country_col])
row_sums = num_df[mbti_cols].sum(axis=1)
mean_sum = row_sums.mean(skipna=True)

if abs(me

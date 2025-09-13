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

if abs(mean_sum - 1) < 0.05:
    value_type = "proportion"
    work_df = num_df.copy()
elif abs(mean_sum - 100) < 5:
    value_type = "percent"
    work_df = num_df.copy()
    work_df[mbti_cols] = work_df[mbti_cols] / 100.0
else:
    value_type = "count"
    work_df, _ = infer_to_proportion(num_df, mbti_cols)

st.sidebar.write(f"**값 유형 추정:** {value_type}")

sel_type = st.sidebar.selectbox("MBTI 유형 선택", MBTI_TYPES, index=MBTI_TYPES.index("INFP"))
work_df["__country__"] = df[country_col].astype(str)
ranked = work_df[["__country__", sel_type]].rename(columns={sel_type: "share"}).dropna()
ranked = ranked.sort_values("share", ascending=False).head(10)
ranked["percent"] = (ranked["share"] * 100).round(2)

base = alt.Chart(ranked).encode(
    x=alt.X("share:Q", title="비율", axis=alt.Axis(format=".0%")),
    y=alt.Y("__country__:N", sort="-x", title="국가"),
    tooltip=["__country__", "percent"],
)

bars = base.mark_bar().interactive()
text = base.mark_text(align="left", dx=3).encode(text="percent")

st.subheader(f"{sel_type} 비율이 가장 높은 국가 Top 10")
st.altair_chart(bars + text, use_container_width=True)

st.divider()
st.markdown("### 결과 데이터")
st.dataframe(ranked, use_container_width=True)

csv = ranked.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="Top 10 결과 CSV 다운로드",
    data=csv,
    file_name=f"mbti_top10_{sel_type}.csv",
    mime="text/csv",
)

with st.expander("진단 정보 보기"):
    st.write({
        "country_col": country_col,
        "mbti_cols_found": mbti_cols,
        "mean_row_sum_before_norm": float(mean_sum) if pd.notna(mean_sum) else None,
        "value_type_inferred": value_type,
    })

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import xml.etree.ElementTree as ET


# =====================================================
# 1. 설정
# =====================================================

URL = "https://apis.data.go.kr/6300000/rest/getTrafficInfoAll"

API_KEY = os.environ["DATA_API_KEY"]


# 나중에 분석 대상으로 선정한 링크 ID 입력
# 아직 선정 전이면 일단 테스트용 링크 몇 개만 넣어도 됩니다.
TARGET_LINK_IDS = [
    "1830000100",
    "1830000200",
    "1830000301"
]


# CSV 저장 위치
SAVE_FOLDER = "data"
SAVE_FILE = os.path.join(
    SAVE_FOLDER,
    "traffic_raw.csv"
)


# =====================================================
# 2. API 호출
# =====================================================

params = {
    "serviceKey": API_KEY
}

response = requests.get(
    URL,
    params=params,
    timeout=60
)

response.raise_for_status()


# =====================================================
# 3. XML 파싱
# =====================================================

root = ET.fromstring(response.content)

rows = []

# 실제 XML 구조에 <TRAFFIC> 단위로 데이터가 들어 있음
for traffic in root.findall(".//TRAFFIC"):

    row = {}

    for child in traffic:
        row[child.tag] = child.text

    rows.append(row)


df = pd.DataFrame(rows)

if df.empty:
    raise ValueError(
        "API 응답에서 교통 데이터를 찾지 못했습니다."
    )


# =====================================================
# 4. 필요한 링크만 선택
# =====================================================

df["linkID"] = df["linkID"].astype(str)

df = df[
    df["linkID"].isin(TARGET_LINK_IDS)
].copy()


# =====================================================
# 5. 수집 시각 추가
# =====================================================

kst = ZoneInfo("Asia/Seoul")

collection_time = datetime.now(
    kst
).strftime("%Y-%m-%d %H:%M:%S")

df.insert(
    0,
    "timestamp",
    collection_time
)


# =====================================================
# 6. 숫자형 컬럼 변환
# =====================================================

numeric_columns = [
    "congestion",
    "linkLength",
    "linkSqc",
    "speed",
    "travelT",
    "udType"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# =====================================================
# 7. CSV 누적 저장
# =====================================================

os.makedirs(
    SAVE_FOLDER,
    exist_ok=True
)

file_exists = os.path.exists(
    SAVE_FILE
)

df.to_csv(
    SAVE_FILE,
    mode="a",
    header=not file_exists,
    index=False,
    encoding="utf-8-sig"
)


print(
    f"[{collection_time}] "
    f"{len(df)}개 링크 저장 완료"
)

print(
    f"저장 위치: {SAVE_FILE}"
)

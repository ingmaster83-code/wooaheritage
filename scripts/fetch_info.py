#!/usr/bin/env python3
"""
fetch_info.py - 전국관광안내소표준데이터 수집 (지자체)

wooaheritage에 향토유산·박물관미술관·관광지와 나란히 "문화관광" 네 번째 카테고리로 추가.

사용법:
  python scripts/fetch_info.py
"""
import sys, json, time
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding="utf-8")

PUBLIC_DATA_PK = "15013112"
SVC_TABLE = "tn_pubr_public_trsmic_api"
COLUMNS = [
    "TRSMIC_NM", "TRSMIC_LC", "CTPRVN_NM", "SIGNGU_NM", "TRSMIC_INTRCN",
    "ADI_SVC_INFO", "RSTDE", "SUMMER_OPER_OPEN_HHMM", "SUMMER_OPER_CLOSE_HHMM",
    "WINTER_OPER_OPEN_HHMM", "WINTER_OPER_CLOSE_HHMM", "ENG_GUIDANCE_YN",
    "JP_GUIDANCE_YN", "CH_GUIDANCE_YN", "GUIDANCE_PHONE_NUMBER", "RDNMADR",
    "LNMADR", "OPER_INSTITUTION_NM", "HOMEPAGE_URL", "LATITUDE", "LONGITUDE",
    "REFERENCE_DATE",
]
OUT_FILE = Path(__file__).parent.parent / "_rawdata" / "info_raw.json"
PER_PAGE = 10000


def fetch_page(page: int) -> list:
    params = [("publicDataPk", PUBLIC_DATA_PK)]
    params += [("colNmList", c) for c in COLUMNS]
    params += [
        ("totalCount", "99999"),
        ("svcTableNm", SVC_TABLE),
        ("perPage", str(PER_PAGE)),
        ("page", str(page)),
    ]
    resp = requests.get(
        "https://www.data.go.kr/download/standard.json",
        params=params, timeout=60,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        return []
    return data


def main():
    print("=== 전국관광안내소표준데이터 수집 시작 ===")
    all_items = []
    page = 1
    while True:
        items = fetch_page(page)
        if not items:
            break
        all_items.extend(items)
        print(f"  페이지 {page}: {len(items)}개 (누적 {len(all_items)})")
        if len(items) < PER_PAGE:
            break
        page += 1
        time.sleep(0.3)

    if not all_items:
        raise SystemExit("수집된 데이터가 없습니다.")

    if OUT_FILE.exists():
        existing = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        if len(all_items) < len(existing) * 0.5:
            raise SystemExit(
                f"수집 건수({len(all_items)}건)가 기존 데이터({len(existing)}건)의 절반 미만입니다. "
                "오류로 판단하여 저장을 중단합니다."
            )

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n완료: {OUT_FILE}")
    print(f"  총 {len(all_items)}개 관광안내소 저장")


if __name__ == "__main__":
    main()

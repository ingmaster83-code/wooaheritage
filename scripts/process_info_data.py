#!/usr/bin/env python3
"""
process_info_data.py - 관광안내소 원본 데이터를 Jekyll 페이지 생성용 JSON으로 가공

입력: _rawdata/info_raw.json
출력: _rawdata/info.json (개별 페이지 생성용), info_search_index.json (지역별 목록 페이지용)

사용법:
  python scripts/process_info_data.py
"""
import json, re, hashlib, sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
RAW = ROOT / "_rawdata" / "info_raw.json"
OUT = ROOT / "_rawdata" / "info.json"
SEARCH_INDEX_OUT = ROOT / "info_search_index.json"

DO_MAP = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "강원도": "강원",
    "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라북도": "전북", "전라남도": "전남",
    "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주",
    "전남광주통합특별시": "광주",
}


def make_slug(name: str, addr: str) -> str:
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    h = hashlib.md5(f"{name}|{addr}".encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{h}" if slug else h


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    items = []
    seen_slugs = Counter()
    skipped = 0
    for d in raw:
        # 필드명 주의: Jekyll 내장 Page.name과 충돌하므로 "infoName" 사용
        info_name = (d.get("TRSMIC_NM") or "").strip()
        addr = (d.get("RDNMADR") or "").strip() or (d.get("LNMADR") or "").strip()
        do_full = (d.get("CTPRVN_NM") or "").strip()
        sggu = (d.get("SIGNGU_NM") or "").strip()
        do_short = DO_MAP.get(do_full, do_full if do_full in DO_MAP.values() else None)
        if not info_name or not do_short:
            skipped += 1
            continue

        slug = make_slug(info_name, addr or sggu)
        seen_slugs[slug] += 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"

        langs = []
        if (d.get("ENG_GUIDANCE_YN") or "").strip() == "Y":
            langs.append("영어")
        if (d.get("JP_GUIDANCE_YN") or "").strip() == "Y":
            langs.append("일본어")
        if (d.get("CH_GUIDANCE_YN") or "").strip() == "Y":
            langs.append("중국어")

        items.append({
            "infoName": info_name,
            "location": (d.get("TRSMIC_LC") or "").strip(),
            "doShort": do_short,
            "doFull": do_full,
            "sigungu": sggu,
            "addr": addr,
            "lat": (d.get("LATITUDE") or "").strip(),
            "lng": (d.get("LONGITUDE") or "").strip(),
            "tel": (d.get("GUIDANCE_PHONE_NUMBER") or "").strip(),
            "operInstitution": (d.get("OPER_INSTITUTION_NM") or "").strip(),
            "homepage": (d.get("HOMEPAGE_URL") or "").strip(),
            "intro": (d.get("TRSMIC_INTRCN") or "").strip(),
            "adiSvc": (d.get("ADI_SVC_INFO") or "").strip(),
            "restDay": (d.get("RSTDE") or "").strip(),
            "summerOpen": (d.get("SUMMER_OPER_OPEN_HHMM") or "").strip(),
            "summerClose": (d.get("SUMMER_OPER_CLOSE_HHMM") or "").strip(),
            "winterOpen": (d.get("WINTER_OPER_OPEN_HHMM") or "").strip(),
            "winterClose": (d.get("WINTER_OPER_CLOSE_HHMM") or "").strip(),
            "langs": langs,
            "refDate": (d.get("REFERENCE_DATE") or "").strip(),
            "slug": slug,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"관광안내소 {len(items)}개 저장 → {OUT}  (제외: {skipped}건)")

    do_counts = Counter(i["doShort"] for i in items)
    print("\n지역별 수:")
    for do, cnt in sorted(do_counts.items(), key=lambda x: -x[1]):
        print(f"  {do}: {cnt}개")

    index = [
        {
            "n": i["infoName"], "slug": i["slug"], "doShort": i["doShort"],
            "sigungu": i["sigungu"], "addr": i["addr"], "langs": i["langs"],
        }
        for i in items
    ]
    SEARCH_INDEX_OUT.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"\n검색 인덱스 {len(index)}건 저장 → {SEARCH_INDEX_OUT}")


if __name__ == "__main__":
    main()

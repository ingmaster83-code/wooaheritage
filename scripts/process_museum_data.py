#!/usr/bin/env python3
"""
process_museum_data.py - 박물관·미술관 원본 데이터를 Jekyll 페이지 생성용 JSON으로 가공

입력: _rawdata/museum_raw.json
출력: _rawdata/museum.json (개별 페이지 생성용), museum_search_index.json (지역별 목록 페이지용)

⚠ heritage와 검색 인덱스를 공유하지 않음 — search_index.json에 합치면 향토유산
지역 페이지에 박물관이 섞여 나와버림. museum 전용 파일을 별도로 둠.

사용법:
  python scripts/process_museum_data.py
"""
import json, re, hashlib, sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
RAW = ROOT / "_rawdata" / "museum_raw.json"
OUT = ROOT / "_rawdata" / "museum.json"
SEARCH_INDEX_OUT = ROOT / "museum_search_index.json"

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


def extract_sigungu(addr: str) -> str:
    if not addr:
        return ""
    for p in addr.split()[1:3]:
        if p.endswith(("시", "군", "구")):
            return p
    return ""


def _hm(v: str) -> str:
    v = (v or "").strip()
    if len(v) == 4 and v.isdigit():
        return f"{v[:2]}:{v[2:]}"
    return v


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    items = []
    seen_slugs = Counter()
    skipped = 0
    for d in raw:
        # 필드명 주의: Jekyll 내장 Page.name과 충돌하므로 "museumName" 사용
        museum_name = (d.get("FCLTY_NM") or "").strip()
        addr = (d.get("RDNMADR") or "").strip() or (d.get("LNMADR") or "").strip()
        if not museum_name or not addr:
            skipped += 1
            continue

        do_full = addr.split()[0]
        do_short = DO_MAP.get(do_full)
        if do_short is None:
            skipped += 1
            continue
        sigungu = extract_sigungu(addr)

        slug = make_slug(museum_name, addr)
        seen_slugs[slug] += 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"

        items.append({
            "museumName": museum_name,
            "type": (d.get("FCLTY_TYPE") or "").strip(),   # 박물관/미술관/기타
            "doShort": do_short,
            "doFull": do_full,
            "sigungu": sigungu,
            "addr": addr,
            "lat": (d.get("LATITUDE") or "").strip(),
            "lng": (d.get("LONGITUDE") or "").strip(),
            "tel": (d.get("OPER_PHONE_NUMBER") or d.get("PHONE_NUMBER") or "").strip(),
            "operInstitution": (d.get("OPER_INSTITUTION_NM") or "").strip(),
            "homepage": (d.get("HOMEPAGE_URL") or "").strip(),
            "facilityInfo": (d.get("FCLTY_INFO") or "").strip(),
            "weekdayOpen": _hm(d.get("WEEKDAY_OPER_OPEN_HHMM")),
            "weekdayClose": _hm(d.get("WEEKDAY_OPER_COLSE_HHMM")),
            "holidayOpen": _hm(d.get("HOLIDAY_OPER_OPEN_HHMM")),
            "holidayClose": _hm(d.get("HOLIDAY_CLOSE_OPEN_HHMM")),
            "restInfo": (d.get("RSTDE_INFO") or "").strip(),
            "adultCharge": (d.get("ADULT_CHRGE") or "").strip(),
            "youthCharge": (d.get("YNGBGS_CHRGE") or "").strip(),
            "childCharge": (d.get("CHILD_CHRGE") or "").strip(),
            "etcChargeInfo": (d.get("ETC_CHRGE_INFO") or "").strip(),
            "intro": (d.get("FCLTY_INTRCN") or "").strip(),
            "transportInfo": (d.get("TRNSPORT_INFO") or "").strip(),
            "institution": (d.get("INSTITUTION_NM") or "").strip(),
            "refDate": (d.get("REFERENCE_DATE") or "").strip(),
            "slug": slug,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"박물관·미술관 {len(items)}개 저장 → {OUT}  (제외: {skipped}건)")

    do_counts = Counter(i["doShort"] for i in items)
    print("\n지역별 수:")
    for do, cnt in sorted(do_counts.items(), key=lambda x: -x[1]):
        print(f"  {do}: {cnt}개")

    type_counts = Counter(i["type"] for i in items)
    print("\n유형별 수:")
    for t, cnt in type_counts.most_common():
        print(f"  {t}: {cnt}개")

    index = [
        {
            "n": i["museumName"], "slug": i["slug"], "doShort": i["doShort"],
            "sigungu": i["sigungu"], "addr": i["addr"], "type": i["type"],
        }
        for i in items
    ]
    SEARCH_INDEX_OUT.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"\n검색 인덱스 {len(index)}건 저장 → {SEARCH_INDEX_OUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
process_data.py - 원본 데이터를 Jekyll 페이지 생성용 JSON으로 가공

입력: _rawdata/heritage_raw.json
출력: _rawdata/heritage.json (향토유산 목록), search_index.json (검색용, 루트)

참고: PIC_INFO 컬럼은 실제 이미지 URL이 아니라 지자체 관광사이트의 "자세히 보기"
링크(예: tour.paju.go.kr/...)라서 <img>로 못 쓰고 외부링크로만 사용한다.

사용법:
  python scripts/process_data.py
"""
import json, re, hashlib, sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
RAW = ROOT / "_rawdata" / "heritage_raw.json"
OUT = ROOT / "_rawdata" / "heritage.json"
SEARCH_INDEX_OUT = ROOT / "search_index.json"

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


def make_slug(name: str, addr: str, appn_no: str) -> str:
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    h = hashlib.md5(f"{name}|{addr}|{appn_no}".encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{h}" if slug else h


def extract_sigungu(addr: str) -> str:
    if not addr:
        return ""
    for p in addr.split()[1:3]:
        if p.endswith(("시", "군", "구")):
            return p
    return ""


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    items = []
    seen_slugs = Counter()
    skipped = 0
    for d in raw:
        # 필드명 주의: Jekyll 내장 Page.name과 충돌하므로 "heritageName" 사용
        heritage_name = (d.get("RELICS_NM") or "").strip()
        addr = (d.get("RDNMADR") or "").strip() or (d.get("LNMADR") or "").strip()
        if not heritage_name or not addr:
            skipped += 1
            continue

        do_full = addr.split()[0]
        do_short = DO_MAP.get(do_full)
        if do_short is None:
            # 주소 표기 오류(오타 등)로 17개 시도명과 매칭 안 되는 소수 레코드는 건너뜀
            skipped += 1
            continue
        sigungu = extract_sigungu(addr)

        appn_no = (d.get("APPN_NO") or "").strip()
        slug = make_slug(heritage_name, addr, appn_no)
        seen_slugs[slug] += 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"

        ref_link = (d.get("PIC_INFO") or "").strip()
        if not ref_link.startswith("http"):
            ref_link = ""

        items.append({
            "heritageName": heritage_name,
            "kind": (d.get("RELICS_KND") or "").strip(),       # 향토유산구분: 기념물/유형문화유적 등
            "type": (d.get("RELICS_SE") or "").strip(),        # 향토유산종류: 옛무덤/건조물 등
            "doShort": do_short,
            "doFull": do_full,
            "sigungu": sigungu,
            "addr": addr,
            "lat": (d.get("LATITUDE") or "").strip(),
            "lng": (d.get("LONGITUDE") or "").strip(),
            "appnNo": appn_no,
            "appnDate": (d.get("APPN_DATE") or "").strip(),
            "posesnSe": (d.get("POSESN_SE") or "").strip(),    # 소유주체: 사유/국유/공유
            "ownerNm": (d.get("OWNER_NM") or "").strip(),
            "scale": (d.get("SCALE") or "").strip(),
            "makePd": (d.get("MAKE_PD") or "").strip(),        # 조성시대
            "intro": (d.get("RELICS_INTRCN") or "").strip(),   # 소개글
            "refLink": ref_link,
            "tel": (d.get("PHONE_NUMBER") or "").strip(),
            "institution": (d.get("INSTITUTION_NM") or "").strip(),
            "refDate": (d.get("REFERENCE_DATE") or "").strip(),
            "slug": slug,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"향토유산 {len(items)}개 저장 → {OUT}  (제외: {skipped}건)")

    do_counts = Counter(i["doShort"] for i in items)
    print("\n지역별 수:")
    for do, cnt in sorted(do_counts.items(), key=lambda x: -x[1]):
        print(f"  {do}: {cnt}개")

    kind_counts = Counter(i["kind"] for i in items)
    print("\n구분별 수:")
    for k, cnt in kind_counts.most_common():
        print(f"  {k}: {cnt}개")

    index = [
        {
            "n": i["heritageName"], "slug": i["slug"], "doShort": i["doShort"],
            "sigungu": i["sigungu"], "addr": i["addr"], "kind": i["kind"], "type": i["type"],
        }
        for i in items
    ]
    SEARCH_INDEX_OUT.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"\n검색 인덱스 {len(index)}건 저장 → {SEARCH_INDEX_OUT}")


if __name__ == "__main__":
    main()

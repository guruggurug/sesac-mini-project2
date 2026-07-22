"""Apply the verified Data A remediation decided on 2026-07-22."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from app.utils.issue_rules import (  # noqa: E402
    calculate_event_severity,
    candidate_content_hash,
    canonicalize_url,
    load_issue_rules,
    normalize_text,
)


SAMSUNG_REPORT_URL = (
    "https://images.samsung.com/is/content/samsung/assets/global/ir/docs/"
    "Samsung_Electronics_Sustainability_Report_2024_ENG.pdf"
)
SK_REPORT_URL = "https://www.skhynix.com/sustainability/UI-FR-SA1601/"
NSSC_URL = "https://www.nssc.go.kr/attach/namo/files/000002/20240926174645693_1E891JFD.pdf"
MOEL_URL = "https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19573"
PIPC_URL = (
    "https://www.pipc.go.kr/np/cop/bbs/selectBoardArticle.do?"
    "bbsId=BS074&mCode=C020010000&nttId=8994"
)


def read_csv(relative_path: str) -> tuple[list[str], list[dict[str, str]]]:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(relative_path: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    path = ROOT / relative_path
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def remediate_esg() -> None:
    fields, rows = read_csv("data/processed/esg_indicators.csv")
    for row in rows:
        if row["source_id"] in {"SRC-0001", "SRC-0002"}:
            row["source_url"] = SAMSUNG_REPORT_URL
        elif row["source_id"] == "SRC-0004":
            row["source_url"] = SK_REPORT_URL
        if row["source_id"] not in {"SRC-0003", "SRC-0005"}:
            continue
        is_samsung = row["company_id"] == "005930"
        row.update(
            {
                "raw_value": "",
                "source_id": "SRC-0002" if is_samsung else "SRC-0004",
                "source_title": (
                    "삼성전자 지속가능경영보고서"
                    if is_samsung
                    else "SK하이닉스 지속가능경영보고서"
                ),
                "source_page": "",
                "source_url": SAMSUNG_REPORT_URL if is_samsung else SK_REPORT_URL,
                "source_table_title": "",
                "source_text": "",
                "assurance": "unknown",
                "availability": "unavailable",
                "data_confidence": "low",
                "note": "기존 DART 임시 접수번호를 폐기했으며 공식 원문 재수집 전 결측 처리",
                "target_value": "",
                "target_unit": "",
                "target_year": "",
                "baseline_value": "",
                "baseline_year": "",
                "target_source_id": "",
            }
        )
    write_csv("data/processed/esg_indicators.csv", fields, rows)


def remediate_sources() -> None:
    fields, rows = read_csv("data/processed/sources.csv")
    replacements = {
        "SRC-0001": {
            "organization_name": "삼성전자",
            "document_title": "Samsung Electronics Sustainability Report 2024 (DS section)",
            "external_id": "",
            "file_name": "Samsung_Electronics_Sustainability_Report_2024_ENG.pdf",
            "url": SAMSUNG_REPORT_URL,
            "validation_method": "official_domain",
            "content_hash": "7d1ebb916e76a93d4f9e8d3aed363b994a4c25d0cfc81dc83b7449ada1804c36",
            "note": "삼성전자 전사 보고서 중 DS 관련 ESG 근거",
        },
        "SRC-0002": {
            "organization_name": "삼성전자",
            "document_title": "Samsung Electronics Sustainability Report 2024",
            "external_id": "",
            "file_name": "Samsung_Electronics_Sustainability_Report_2024_ENG.pdf",
            "url": SAMSUNG_REPORT_URL,
            "validation_method": "official_domain",
            "content_hash": "7d1ebb916e76a93d4f9e8d3aed363b994a4c25d0cfc81dc83b7449ada1804c36",
            "note": "삼성전자 연결 기준 ESG 근거",
        },
        "SRC-0004": {
            "organization_name": "SK하이닉스",
            "document_title": "SK hynix Sustainability Report archive",
            "external_id": "",
            "file_name": "skhynix_sustainability_report_archive.html",
            "url": SK_REPORT_URL,
            "validation_method": "official_domain",
            "content_hash": "cc3d60fa15f7daaf20dacc1f68ae2eb983240b15d992e37b1c2f140eca3d494a",
            "note": "SK하이닉스 공식 지속가능경영보고서 보관 페이지",
        },
        "SRC-0006": {
            "external_id": "201",
            "file_name": "nssc_201_samsung_radiation.pdf",
            "url": NSSC_URL,
            "content_hash": "f2c9bc122381908b1b5524f7259ed75b92f9e98f99717630e1ce486a5ea2dea8",
            "note": "원안위 제201회 회의 삼성전자 기흥사업장 방사선 피폭 조사·처분 자료",
        },
        "SRC-0008": {
            "external_id": "19573",
            "file_name": "moel_19573_skhynix_fluorine_inspection.html",
            "url": MOEL_URL,
            "content_hash": "44fe001e0227990956b6d21a3181907d7c67d7b517f8124928ddf9dd61cfe618",
            "note": "고용노동부 반도체 제조업 25개소 집중 점검 착수 보도자료",
        },
        "SRC-0010": {
            "external_id": "8994",
            "file_name": "pipc_8994_samsung_privacy.html",
            "url": PIPC_URL,
            "content_hash": "df894e579cbee876084c0997683b6f35c8d0e708a22652751ab8f00248e0cd02",
            "note": "개인정보위 삼성전자 개인정보 보호법 위반 제재 보도자료",
        },
    }
    retained = []
    for row in rows:
        replacement = replacements.get(row["source_id"])
        if not replacement:
            continue
        row.update(replacement)
        retained.append(row)
    write_csv("data/processed/sources.csv", fields, retained)


def _event(row: dict[str, str], **updates: str) -> dict[str, str]:
    row.update(updates)
    rules = load_issue_rules()
    severity, _ = calculate_event_severity(row, rules)
    row["severity"] = str(severity)
    row["severity_rule_version"] = rules["version"]
    return row


def remediate_events() -> None:
    fields, rows = read_csv("data/processed/events.csv")
    by_id = {row["event_id"]: row for row in rows}
    retained = [
        _event(
            by_id["EVT-0001"],
            status="confirmed",
            enforcement_action="fine",
            official_source_url=NSSC_URL,
            resolved_date="",
            note="원안위 제201회 회의 조사결과와 과태료 처분 확인",
        ),
        _event(
            by_id["EVT-0003"],
            event_date="2026-06-26",
            event_date_type="authority_announcement_date",
            status="confirmed",
            enforcement_action="investigation",
            official_source_url=MOEL_URL,
            news_url="",
            summary="고용노동부가 반복 불소 누출 사고와 관련해 SK하이닉스 등 반도체 제조업 25개소 집중 점검에 착수",
            note="점검 착수 공식 발표만 확인되어 해결 상태로 분류하지 않음",
            severity_evidence="반복 불소 누출 사고에 따른 정부 집중점검 착수",
            responsibility_evidence="공식 발표에서 SK하이닉스를 점검 대상으로 명시",
            persistence_evidence="점검 결과와 후속 처분은 아직 확인되지 않음",
            resolved_date="",
            market_event_date="2026-06-26",
            market_event_date_type="authority_announcement_date",
        ),
        _event(
            by_id["EVT-0005"],
            event_date="2023-06-28",
            event_date_type="authority_announcement_date",
            status="confirmed",
            enforcement_action="fine",
            official_source_url=PIPC_URL,
            news_url="",
            summary="개인정보위가 삼성전자 개인정보 유출과 안전조치의무 위반에 과징금·과태료 및 시정조치를 의결",
            note="개인정보위 2023년 6월 28일 공식 보도자료 확인",
            severity_evidence="과징금 8억 7,558만원과 과태료 1,400만원 및 시정조치",
            responsibility_evidence="시스템 오류와 안전조치의무 이행 미흡이 공식 확인됨",
            persistence_evidence="재발 방지대책 수립 명령 단계이며 완료 여부는 확인되지 않음",
            resolved_date="",
            market_event_date="2023-06-28",
            market_event_date_type="authority_announcement_date",
        ),
    ]
    write_csv("data/processed/events.csv", fields, retained)


def _candidate(
    row: dict[str, str],
    *,
    status: str,
    matched_event_id: str = "",
    rejection_reason: str = "",
) -> dict[str, str]:
    row["validation_status"] = status
    row["matched_event_id"] = matched_event_id
    row["rejection_reason"] = rejection_reason
    row["normalized_title"] = normalize_text(row["title"])
    row["canonical_url"] = canonicalize_url(row["url"])
    row["source_name"] = urlsplit(row["url"]).netloc.lower()
    row["content_hash"] = candidate_content_hash(row)
    return row


def remediate_candidates() -> None:
    fields, rows = read_csv("data/candidate/news_candidates.csv")
    by_id = {row["candidate_id"]: row for row in rows}
    output = [
        _candidate(by_id["CND-0001"], status="validated", matched_event_id="EVT-0001"),
        _candidate(
            by_id["CND-0002"],
            status="rejected",
            rejection_reason="환경부 공식 원문과 사건 세부내용을 확인하지 못함",
        ),
        _candidate(
            {
                **by_id["CND-0003"],
                "source_name": "www.moel.go.kr",
                "external_id": "19573",
                "title": "고용노동부, 반복 불소 누출 사고 관련 반도체 제조업 집중 점검 착수",
                "published_at": "2026-06-26",
                "url": MOEL_URL,
                "description": "SK하이닉스 등 반도체 제조업 25개소에 대한 집중 점검 착수 공식 발표",
            },
            status="validated",
            matched_event_id="EVT-0003",
        ),
        _candidate(
            by_id["CND-0004"],
            status="rejected",
            rejection_reason="공정위 공식 원문과 사건 세부내용을 확인하지 못함",
        ),
        _candidate(
            by_id["CND-0005"],
            status="rejected",
            rejection_reason="공식 출처와 일치하는 처리 사건 없음",
        ),
    ]
    pipc_candidate = {
        "candidate_id": "CND-0006",
        "company_id": "005930",
        "company_name": "삼성전자",
        "detection_source_type": "news",
        "source_name": "www.pipc.go.kr",
        "external_id": "8994",
        "query": "삼성전자 개인정보 보호법 위반 제재",
        "title": "개인정보 보호법을 위반한 삼성전자 등 2개 사업자 제재",
        "normalized_title": "",
        "published_at": "2023-06-28",
        "collected_at": "2026-07-22T00:00:00+09:00",
        "url": PIPC_URL,
        "canonical_url": "",
        "description": "개인정보위 과징금·과태료 및 시정조치 공식 발표",
        "content_hash": "",
        "validation_status": "",
        "matched_event_id": "",
        "rejection_reason": "",
    }
    output.append(_candidate(pipc_candidate, status="validated", matched_event_id="EVT-0005"))
    write_csv("data/candidate/news_candidates.csv", fields, output)


def remediate_event_sources() -> None:
    fields, _ = read_csv("data/processed/event_sources.csv")
    rows = [
        {
            "event_id": "EVT-0001",
            "source_id": "SRC-0006",
            "source_role": "official_confirmation",
            "is_primary": "true",
            "note": "원안위 제201회 회의 조사결과 및 처분 자료",
        },
        {
            "event_id": "EVT-0001",
            "source_id": "SRC-0001",
            "source_role": "context",
            "is_primary": "false",
            "note": "삼성전자 DS ESG·안전관리 배경자료",
        },
        {
            "event_id": "EVT-0003",
            "source_id": "SRC-0008",
            "source_role": "official_confirmation",
            "is_primary": "true",
            "note": "고용노동부 집중 점검 착수 공식 보도자료",
        },
        {
            "event_id": "EVT-0005",
            "source_id": "SRC-0010",
            "source_role": "official_confirmation",
            "is_primary": "true",
            "note": "개인정보위 삼성전자 제재 공식 보도자료",
        },
    ]
    write_csv("data/processed/event_sources.csv", fields, rows)


def main() -> None:
    remediate_esg()
    remediate_sources()
    remediate_events()
    remediate_candidates()
    remediate_event_sources()


if __name__ == "__main__":
    main()

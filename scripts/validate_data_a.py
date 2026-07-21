import csv
import os
import sys
import re

def validate_esg_indicators(filepath):
    print(f"[+] Validating ESG Indicators CSV: {filepath}")
    if not os.path.exists(filepath):
        print(f"[-] ERROR: File not found: {filepath}")
        return False

    required_headers = [
        "company_id", "company_name", "indicator_id", "category", "indicator_name",
        "raw_value", "raw_unit", "period", "business_scope", "geography",
        "source_type", "source_title", "source_page", "source_url", "assurance",
        "scope_mismatch", "availability", "data_confidence", "risk_direction",
        "review_status", "note"
    ]

    valid_companies = {"005930": "삼성전자", "000660": "SK하이닉스"}
    valid_categories = {"E", "S", "G"}
    valid_scopes = {"DS", "semiconductor", "domestic_site", "consolidated", "unknown"}
    valid_geographies = {"Korea", "global", "mixed", "unknown"}
    valid_availabilities = {"available", "unavailable"}
    valid_confidences = {"high", "medium", "low"}
    valid_directions = {"higher_is_worse", "higher_is_better", "event_based", "qualitative"}
    valid_statuses = {"pending", "needs_review", "approved", "rejected"}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if headers != required_headers:
            print(f"[-] ERROR: Header mismatch.\nExpected: {required_headers}\nGot: {headers}")
            return False

        rows = list(reader)
        if len(rows) < 12:
            print(f"[-] WARNING/ERROR: Row count {len(rows)} is less than recommended 12 rows.")

        company_counts = {"005930": 0, "000660": 0}

        for idx, row in enumerate(rows, start=2):
            cid = row["company_id"]
            if cid not in valid_companies:
                print(f"[-] ERROR line {idx}: Invalid company_id '{cid}'")
                return False
            if row["company_name"] != valid_companies[cid]:
                print(f"[-] ERROR line {idx}: Mismatched company_name '{row['company_name']}' for '{cid}'")
                return False
            company_counts[cid] += 1

            if not re.match(r"^[ESG][0-9]{2}$", row["indicator_id"]):
                print(f"[-] ERROR line {idx}: Invalid indicator_id '{row['indicator_id']}'")
                return False

            if row["category"] not in valid_categories:
                print(f"[-] ERROR line {idx}: Invalid category '{row['category']}'")
                return False

            if row["business_scope"] not in valid_scopes:
                print(f"[-] ERROR line {idx}: Invalid business_scope '{row['business_scope']}'")
                return False

            scope_mismatch = row["scope_mismatch"].strip().lower() == "true"
            if cid == "005930" and row["business_scope"] == "consolidated" and not scope_mismatch:
                print(f"[-] ERROR line {idx}: Samsung consolidated must have scope_mismatch=true")
                return False

            if row["availability"] not in valid_availabilities:
                print(f"[-] ERROR line {idx}: Invalid availability '{row['availability']}'")
                return False

            if row["availability"] == "available":
                try:
                    float(row["raw_value"])
                except ValueError:
                    print(f"[-] ERROR line {idx}: raw_value '{row['raw_value']}' is not a valid number for available indicator")
                    return False
            else:
                if row["raw_value"] != "" and row["raw_value"] is not None:
                    print(f"[-] ERROR line {idx}: unavailable indicator must have empty raw_value")
                    return False

            if row["data_confidence"] not in valid_confidences:
                print(f"[-] ERROR line {idx}: Invalid data_confidence '{row['data_confidence']}'")
                return False

            if row["risk_direction"] not in valid_directions:
                print(f"[-] ERROR line {idx}: Invalid risk_direction '{row['risk_direction']}'")
                return False

            if row["review_status"] not in valid_statuses:
                print(f"[-] ERROR line {idx}: Invalid review_status '{row['review_status']}'")
                return False

    print(f"[+] ESG Indicators validation PASSED! Total rows: {len(rows)} (005930: {company_counts['005930']}, 000660: {company_counts['000660']})")
    return True


def validate_events(filepath):
    print(f"\n[+] Validating Events CSV: {filepath}")
    if not os.path.exists(filepath):
        print(f"[-] ERROR: File not found: {filepath}")
        return False

    required_headers = [
        "event_id", "company_id", "company_name", "event_category", "event_subcategory",
        "event_date", "event_date_type", "business_unit", "status", "severity",
        "authority_confirmed", "official_source_url", "news_url", "summary",
        "review_status", "note"
    ]

    valid_companies = {"005930": "삼성전자", "000660": "SK하이닉스"}
    valid_statuses = {"rumor", "reported", "confirmed", "sanctioned", "resolved"}
    valid_date_types = {
        "occurrence_date", "official_disclosure_date", "authority_announcement_date",
        "first_public_report_date", "sanction_date", "resolution_date"
    }

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if headers != required_headers:
            print(f"[-] ERROR: Header mismatch.\nExpected: {required_headers}\nGot: {headers}")
            return False

        rows = list(reader)
        if len(rows) < 4:
            print(f"[-] WARNING: Row count {len(rows)} is less than recommended 4 events.")

        for idx, row in enumerate(rows, start=2):
            if not re.match(r"^EVT-[0-9]{4}$", row["event_id"]):
                print(f"[-] ERROR line {idx}: Invalid event_id '{row['event_id']}'")
                return False

            cid = row["company_id"]
            if cid not in valid_companies:
                print(f"[-] ERROR line {idx}: Invalid company_id '{cid}'")
                return False

            if row["event_date_type"] not in valid_date_types:
                print(f"[-] ERROR line {idx}: Invalid event_date_type '{row['event_date_type']}'")
                return False

            if row["status"] not in valid_statuses:
                print(f"[-] ERROR line {idx}: Invalid status '{row['status']}'")
                return False

            auth_confirmed = row["authority_confirmed"].strip().lower() == "true"
            if row["status"] in {"confirmed", "sanctioned", "resolved"} and not auth_confirmed:
                print(f"[-] ERROR line {idx}: Status '{row['status']}' requires authority_confirmed=true")
                return False

            try:
                sev = int(row["severity"])
                if not (1 <= sev <= 5):
                    print(f"[-] ERROR line {idx}: severity '{sev}' out of range 1-5")
                    return False
            except ValueError:
                print(f"[-] ERROR line {idx}: severity '{row['severity']}' is not an integer")
                return False

    print(f"[+] Events validation PASSED! Total events: {len(rows)}")
    return True


def validate_sources(filepath):
    print(f"\n[+] Validating Sources CSV: {filepath}")
    if not os.path.exists(filepath):
        print(f"[-] ERROR: File not found: {filepath}")
        return False

    required_headers = [
        "source_id", "company_name", "source_type", "document_title",
        "publication_year", "file_name", "url", "reviewed", "note"
    ]

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if headers != required_headers:
            print(f"[-] ERROR: Header mismatch.\nExpected: {required_headers}\nGot: {headers}")
            return False
        rows = list(reader)

    print(f"[+] Sources validation PASSED! Total sources: {len(rows)}")
    return True


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    esg_file = os.path.join(base_dir, "data", "reviewed", "esg_indicators.csv")
    events_file = os.path.join(base_dir, "data", "reviewed", "events.csv")
    sources_file = os.path.join(base_dir, "data", "reviewed", "sources.csv")

    res_esg = validate_esg_indicators(esg_file)
    res_evt = validate_events(events_file)
    res_src = validate_sources(sources_file)

    if res_esg and res_evt and res_src:
        print("\n==========================================")
        print(" ALL DATA A DATASETS PASSED VALIDATION! ")
        print("==========================================")
        sys.exit(0)
    else:
        print("\n==========================================")
        print(" DATA A VALIDATION FAILED! ")
        print("==========================================")
        sys.exit(1)

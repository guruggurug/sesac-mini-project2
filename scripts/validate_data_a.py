import os
import sys

# Add src/backend to import paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "backend"))

try:
    from app.utils.csv_validator import validate_data_a_bundle
    from app.core.exceptions import CSVValidationError
except ImportError as e:
    print(f"Error importing validation modules: {e}")
    print("Please make sure you have the virtual environment activated or python path configured properly.")
    sys.exit(1)


def main():
    print(f"[+] Starting Data A Bundle Validation (Base Dir: {BASE_DIR})")
    try:
        bundle = validate_data_a_bundle(BASE_DIR)
        print("[+] Data A bundle validation PASSED!")
        print(f"  - candidates: {len(bundle['candidates'])} rows (data/candidate/news_candidates.csv)")
        print(f"  - sources: {len(bundle['sources'])} rows (data/processed/sources.csv)")
        print(f"  - event_sources: {len(bundle['event_sources'])} rows (data/processed/event_sources.csv)")
        print(f"  - events: {len(bundle['events'])} rows (data/processed/events.csv)")
        print(f"  - esg: {len(bundle['esg'])} rows (data/processed/esg_indicators.csv)")
        sys.exit(0)
    except CSVValidationError as e:
        print("\n[-] DATA A VALIDATION FAILED!")
        print(f"  - Error Code: {e.code}")
        print(f"  - Error Message: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Fatal error during validation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

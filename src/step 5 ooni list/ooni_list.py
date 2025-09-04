import requests
import csv
import re
import logging
from datetime import datetime, timedelta

OUTPUT_FILE = "sum/input/ooni_domains.lst"
EXCLUDE_FILE = "sum/input/ooni_exclude_domains.lst"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ooni_domain_fetch.log", mode="a"),
              logging.StreamHandler()]
)

def normalize_domain(domain: str) -> str:
    return domain.lstrip("www.") if domain.startswith("www.") else domain

def load_suffix_exclusions(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            items = []
            for line in f:
                s = line.strip().lower()
                if not s or s.startswith("#"):
                    continue
                if s.startswith("*."):
                    s = s[2:]
                items.append(s)
            return set(items)
    except FileNotFoundError:
        return set()

def is_excluded(domain: str, excludes: set) -> bool:
    d = domain.lower()
    return any(d == suf or d.endswith("." + suf) for suf in excludes)

def fetch_and_process_ooni_domains(output_file: str):
    try:
        today = datetime.now()
        until_date = today.strftime("%Y-%m-%d")
        since_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")

        base_url = "https://api.ooni.io/api/v1/aggregation"
        params = {
            "axis_y": "domain",
            "axis_x": "measurement_start_day",
            "probe_cc": "RU",
            "since": since_date,
            "until": until_date,
            "test_name": "web_connectivity",
            "time_grain": "day",
            "format": "CSV",
        }

        url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        logging.info(f"Fetching OONI data: {url}")

        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to download data, status: {response.status_code}")
            return

        domains = set()
        csv_data = response.content.decode("utf-8").splitlines()
        csv_reader = csv.DictReader(csv_data)

        pattern = r"^.*\.{2,}.*$"
        excludes = load_suffix_exclusions(EXCLUDE_FILE)

        for row in csv_reader:
            domain = row["domain"].strip()
            anomaly_count = int(row["anomaly_count"])
            ok_count = int(row["ok_count"])

            logging.info(
                f"Checking: {domain} | Anomalies: {anomaly_count}, OK: {ok_count}"
            )

            if re.match(pattern, domain):
                continue
            if domain.endswith("yandex.net") or domain.endswith("yandex.ru"):
                continue
            if is_excluded(domain, excludes):
                continue

            if anomaly_count > ok_count:
                normalized = normalize_domain(domain)
                if normalized not in domains:
                    domains.add(normalized)

        with open(output_file, "w", encoding="utf-8") as output:
            for domain in sorted(domains):
                output.write(f"{domain}\n")

        print(f"Total unique domains written: {len(domains)}")

    except Exception as e:
        logging.error(f"Error occurred: {e}")

if __name__ == "__main__":
    fetch_and_process_ooni_domains(OUTPUT_FILE)

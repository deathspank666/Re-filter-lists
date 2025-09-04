from idna import encode as idna_encode

DOMAINS_FILE = "sum/input/domains.lst"
OONI_FILE = "sum/input/ooni_domains.lst"
COMMUNITY_FILE = "community.lst"
EXCLUDE_FILE = "sum/input/global_exclude_domains.lst"
OUTPUT_FILE = "sum/output/domains_all.lst"

def read_domains_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            domains = []
            for line in f:
                s = line.strip()
                if s and not s.startswith("#"):
                    if s.startswith("*."):
                        s = s[2:]
                    domains.append(s)
            return domains
    except FileNotFoundError:
        return []

def convert_to_punycode(domains):
    punycode_domains = set()
    for domain in domains:
        try:
            puny = idna_encode(domain).decode("utf-8")
            punycode_domains.add(puny)
        except Exception:
            pass
    return punycode_domains

def filter_with_suffixes(domains, excludes):
    out = set()
    for d in domains:
        if any(d == e or d.endswith("." + e) for e in excludes):
            continue
        out.add(d)
    return out

def main():
    domains1 = read_domains_from_file(DOMAINS_FILE)
    domains2 = read_domains_from_file(OONI_FILE)
    domains3 = read_domains_from_file(COMMUNITY_FILE)
    excludes = read_domains_from_file(EXCLUDE_FILE)

    all_domains = set(domains1 + domains2 + domains3)

    unique_domains = convert_to_punycode(all_domains)
    exclude_puny = convert_to_punycode(set(excludes))

    final_domains = filter_with_suffixes(unique_domains, exclude_puny)

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for domain in sorted(final_domains):
                f.write(f"{domain}\n")
    except Exception as e:
        print(f"Error writing output: {e}")

if __name__ == "__main__":
    main()

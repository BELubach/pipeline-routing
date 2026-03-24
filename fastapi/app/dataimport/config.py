
GEM_PIPELINE_FIELD_MAP: dict[str, str] = {
    # GEM field name           → our internal key
    "GEM Unit ID":              "gem_id",
    "Pipeline Name":            "pipeline_name",
    "Segment Name":             "source_name",
    "Operator":                 "operator",
    "Status":                   "gem_status",
    "Diameter (mm)":            "diameter_mm",
    "Max. Capacity (Mm3/d)":    "capacity_mcm_d",
    "Length (km)":              "length_km",
    "Start Year":               "year_built",
    "Countries":                "countries_raw",
}

GEM_STATUS_MAP: dict[str, str] = {
    "Operating":        "operating",
    "Construction":     "construction",
    "Pre-construction": "planned",
    "Proposed":         "planned",
    "Announced":        "planned",
    "Cancelled":        "decommissioned",
    "Shelved":          "decommissioned",
    "Retired":          "decommissioned",
    "Idle":             "decommissioned",
}

# ISO-3166-1 alpha-2 codes for Europe scope filter
EUROPE_COUNTRIES: frozenset[str] = frozenset({
    "AT", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GB", "GR", "HR", "HU", "IE", "IS", "IT", "LT", "LU", "LV", "MK", "MT",
    "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI", "SK", "TR", "UA", "AL",
    "BA", "ME", "MD", "BY", "DZ", "LY", "EG", "MA", "AZ", "GE", "AM",
})

# Country name → ISO-3166-1 alpha-2 (GEM uses full English names)
COUNTRY_NAME_TO_ISO2: dict[str, str] = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Switzerland": "CH",
    "Cyprus": "CY", "Czechia": "CZ", "Czech Republic": "CZ", "Germany": "DE",
    "Denmark": "DK", "Estonia": "EE", "Spain": "ES", "Finland": "FI",
    "France": "FR", "United Kingdom": "GB", "Greece": "GR", "Croatia": "HR",
    "Hungary": "HU", "Ireland": "IE", "Iceland": "IS", "Italy": "IT",
    "Lithuania": "LT", "Luxembourg": "LU", "Latvia": "LV", "North Macedonia": "MK",
    "Malta": "MT", "Netherlands": "NL", "Norway": "NO", "Poland": "PL",
    "Portugal": "PT", "Romania": "RO", "Serbia": "RS", "Sweden": "SE",
    "Slovenia": "SI", "Slovakia": "SK", "Turkey": "TR", "Ukraine": "UA",
    "Albania": "AL", "Bosnia and Herzegovina": "BA", "Montenegro": "ME",
    "Moldova": "MD", "Belarus": "BY", "Algeria": "DZ", "Libya": "LY",
    "Egypt": "EG", "Morocco": "MA", "Azerbaijan": "AZ", "Georgia": "GE",
    "Armenia": "AM", "Russia": "RU", "Kazakhstan": "KZ",
}
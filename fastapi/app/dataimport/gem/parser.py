"""
Translates a raw GeoDataFrame row into a clean intermediate dict
using GEM_PIPELINE_FIELD_MAP.  No DB objects are created here —
this layer is pure data transformation and is trivially unit-testable.
"""

import pandas as pd
from typing import Any

from app.dataimport.config import (
    GEM_PIPELINE_FIELD_MAP,
    GEM_STATUS_MAP,
    EUROPE_COUNTRIES,
    COUNTRY_NAME_TO_ISO2,
)
from app.dataimport.value_parser import ValueParser


class GemPipelineParser:
    """
    Parses a single GeoDataFrame row into a normalised dict
    using the field map and status/country lookups from config.
    """

    def __init__(
        self,
        field_map: dict[str, str] = GEM_PIPELINE_FIELD_MAP,
        status_map: dict[str, str] = GEM_STATUS_MAP,
    ):
        self._field_map = field_map
        self._status_map = status_map
        # Reverse map: our key → GEM field name
        self._reverse = {v: k for k, v in field_map.items()}

    def parse_row(self, row: pd.Series) -> dict[str, Any]:
        """
        Returns a dict with our internal keys, all values coerced.
        Geometry is NOT included — caller handles that separately.
        """
        raw = self._extract_raw(row)
        return {
            "gem_id":        ValueParser.as_str(raw["gem_id"]),
            "pipeline_name": ValueParser.as_str(raw["pipeline_name"]),
            # Fall back to pipeline_name when segment name is absent
            "source_name":   ValueParser.as_str(raw["source_name"])
                             or ValueParser.as_str(raw["pipeline_name"]),
            "operator":      ValueParser.as_str(raw["operator"]),
            "status":        self._map_status(raw["gem_status"]),
            "diameter_mm":   ValueParser.as_int(raw["diameter_mm"]),
            "capacity_mcm_d":ValueParser.as_float(raw["capacity_mcm_d"]),
            "length_km":     ValueParser.as_float(raw["length_km"]),
            "year_built":    ValueParser.as_int(raw["year_built"]),
            "country_codes": self._parse_countries(raw["countries_raw"]),
        }

    def is_in_scope(self, parsed: dict[str, Any]) -> bool:
        """
        Return True if any of the segment's country codes fall within
        EUROPE_COUNTRIES.  Segments with no country data pass through
        (upstream bbox filter is the safety net).
        """
        codes = parsed.get("country_codes") or []
        if not codes:
            return True
        return bool(EUROPE_COUNTRIES.intersection(codes))

    # ── private ───────────────────────────────────────────────────────────────

    def _extract_raw(self, row: pd.Series) -> dict[str, Any]:
        """Pull all mapped fields from the row by GEM field name."""
        return {
            our_key: row.get(gem_field)
            for gem_field, our_key in self._field_map.items()
        }

    def _map_status(self, raw: Any) -> str:
        if ValueParser.is_empty(raw):
            return "operating"
        return self._status_map.get(str(raw).strip(), "operating")

    def _parse_countries(self, raw: Any) -> list[str]:
        """
        Convert GEM's comma-separated full country names to ISO-2 codes,
        keeping only codes present in COUNTRY_NAME_TO_ISO2.
        Unknown names are dropped with a warning rather than crashing.
        """
        if ValueParser.is_empty(raw):
            return []
        codes = []
        for name in str(raw).split(","):
            name = name.strip()
            if not name:
                continue
            iso2 = COUNTRY_NAME_TO_ISO2.get(name)
            if iso2:
                codes.append(iso2)
            else:
                # Keep unresolved names as-is so data isn't silently lost
                codes.append(name)
        return codes
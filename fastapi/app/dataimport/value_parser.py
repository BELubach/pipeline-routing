
import pandas as pd
from typing import Any, Optional


class ValueParser:
    """
    Safe type coercion for raw GeoDataFrame / CSV values.
    All methods return None on missing, NaN, or unparseable input —
    never raise.
    """

    @staticmethod
    def is_empty(val: Any) -> bool:
        """True for None, NaN, empty string, or whitespace-only string."""
        if val is None:
            return True
        try:
            if pd.isna(val):
                return True
        except (TypeError, ValueError):
            pass
        return isinstance(val, str) and not val.strip()

    @staticmethod
    def as_str(val: Any) -> Optional[str]:
        if ValueParser.is_empty(val):
            return None
        return str(val).strip() or None

    @staticmethod
    def as_int(val: Any) -> Optional[int]:
        if ValueParser.is_empty(val):
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def as_float(val: Any) -> Optional[float]:
        if ValueParser.is_empty(val):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
        
    @staticmethod
    def safe_str(val: Any) -> Optional[str]:
        if ValueParser.is_na(val):
            return None
        return str(val).strip() or None
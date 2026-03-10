#!/usr/bin/env python3
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FileSpec:
    label: str
    candidates: tuple[str, ...]
    date_columns: tuple[str, ...] = ("trade_date", "date", "datetime", "time")


def resolve_path(candidates: Iterable[str]) -> Path | None:
    """
    Support both:
    - Windows-style notebook paths like r"data\\AH_premium_analysis.csv"
      (on Linux this can be a literal backslash filename)
    - Normal POSIX paths like "data/AH_premium_analysis.csv"
    """
    for s in candidates:
        p = Path(s)
        if p.exists():
            return p
        # If the candidate contains backslashes, also try interpreting it as a path.
        if "\\" in s:
            p2 = Path(*s.split("\\"))
            if p2.exists():
                return p2
    return None


def max_yyyymmdd_in_csv(path: Path, date_columns: tuple[str, ...]) -> int | None:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return None

        date_col = None
        lower = {c.lower(): c for c in reader.fieldnames}
        for cand in date_columns:
            if cand.lower() in lower:
                date_col = lower[cand.lower()]
                break
        if date_col is None:
            # fallback: try first column
            date_col = reader.fieldnames[0]

        max_date: int | None = None
        for row in reader:
            raw = (row.get(date_col) or "").strip()
            if not raw:
                continue
            # allow "YYYY-MM-DD" or "YYYYMMDD"
            digits = "".join(ch for ch in raw if ch.isdigit())
            if len(digits) < 8:
                continue
            yyyymmdd = int(digits[:8])
            if max_date is None or yyyymmdd > max_date:
                max_date = yyyymmdd
        return max_date


def main() -> int:
    try:
        import my_settings  # type: ignore

        expected_end = int(getattr(my_settings, "date_end"))
    except Exception:
        expected_end = None

    files: list[FileSpec] = [
        FileSpec(
            label="AH premium (analysis)",
            candidates=("data\\AH_premium_analysis.csv", "data/AH_premium_analysis.csv"),
            date_columns=("trade_date",),
        ),
        FileSpec(
            label="A daily k",
            candidates=("data\\AH_stock_daily_A_k.csv", "data/AH_stock_daily_A_k.csv"),
            date_columns=("trade_date", "date"),
        ),
        FileSpec(
            label="HK daily k",
            candidates=("data\\AH_stock_daily_HK_k.csv", "data/AH_stock_daily_HK_k.csv"),
            date_columns=("trade_date", "date"),
        ),
        FileSpec(
            label="USDCNH",
            candidates=("data\\USDCNH_daily.csv", "data/USDCNH_daily.csv"),
            date_columns=("trade_date",),
        ),
        FileSpec(
            label="USDHKD",
            candidates=("data\\USDHKD_daily.csv", "data/USDHKD_daily.csv"),
            date_columns=("trade_date",),
        ),
        FileSpec(
            label="SH300",
            candidates=("data\\SH300_daily_k.csv", "data/SH300_daily_k.csv"),
            date_columns=("trade_date",),
        ),
        FileSpec(
            label="HSI",
            candidates=("data\\HSI_daily_k.csv", "data/HSI_daily_k.csv"),
            date_columns=("trade_date",),
        ),
        FileSpec(
            label="IXIC",
            candidates=("data\\IXIC_daily_k.csv", "data/IXIC_daily_k.csv"),
            date_columns=("trade_date",),
        ),
    ]

    print("Data freshness (max date):")
    if expected_end is not None:
        print(f"- my_settings.date_end = {expected_end}")
    for spec in files:
        p = resolve_path(spec.candidates)
        if p is None:
            print(f"- {spec.label}: (missing)")
            continue
        max_date = max_yyyymmdd_in_csv(p, spec.date_columns)
        if max_date is None:
            print(f"- {spec.label}: (no date)")
            continue
        note = ""
        if expected_end is not None and max_date < expected_end:
            note = "  <-- older than my_settings.date_end (need re-fetch?)"
        print(f"- {spec.label}: {max_date} ({p}){note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


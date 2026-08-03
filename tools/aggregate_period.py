#!/usr/bin/env python3
"""Aggregate valid weekly Family Operating Scores into monthly/yearly reports."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from score_cycle import LABELS, WEIGHTS, calculate, child_signal_gate, classify


DATA_DIR = Path("07-data/weekly")
REPORT_DIR = Path("08-reports")


def load_records() -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Cannot read {path}: {exc}") from exc
        if isinstance(data, dict):
            records.append((path, data))
    return records


def period_key(data: dict[str, Any], kind: str) -> str | None:
    raw_date = str(data.get("date_to") or data.get("date_from") or "")
    try:
        parsed = date.fromisoformat(raw_date)
    except ValueError:
        return None
    if kind == "monthly":
        return f"{parsed.year:04d}-{parsed.month:02d}"
    return f"{parsed.year:04d}"


def aggregate(kind: str, key: str, records: list[tuple[Path, dict[str, Any]]]) -> str:
    selected = [(path, data) for path, data in records if period_key(data, kind) == key]
    scores: list[float] = []
    statuses: Counter[str] = Counter()
    metric_values: dict[str, list[int]] = defaultdict(list)
    safety_weeks: list[str] = []
    insufficient: list[str] = []

    for path, data in selected:
        score, coverage, results, _missing = calculate(data)
        status = classify(score)
        statuses[status] += 1
        if score is not None:
            scores.append(score)
        else:
            insufficient.append(str(data.get("period_id", path.stem)))
        for result in results:
            metric_values[result.key].append(result.score)
        red, _invalid = child_signal_gate(data)
        if red:
            safety_weeks.append(str(data.get("period_id", path.stem)))

    title = "ماهانه" if kind == "monthly" else "سالانه"
    lines = [f"# جمع‌بندی عددی {title} — {key}", ""]
    if not selected:
        return "\n".join(lines + ["هیچ داده هفتگی برای این دوره وجود ندارد.", ""])

    lines.extend(
        [
            "## نمای کلی",
            "",
            f"- تعداد هفته‌های ثبت‌شده: {len(selected)}",
            f"- هفته‌های دارای امتیاز معتبر: {len(scores)}",
        ]
    )
    if scores:
        lines.extend(
            [
                f"- میانگین FOS: {sum(scores) / len(scores):.1f}/100",
                f"- کمینه / بیشینه: {min(scores):.1f} / {max(scores):.1f}",
            ]
        )
    lines.append(f"- وضعیت‌ها: {dict(statuses)}")
    lines.append("")

    averages = []
    for metric, values in metric_values.items():
        if values:
            averages.append((sum(values) / len(values), metric, len(values)))
    averages.sort()

    lines.extend(["## حوزه‌های نیازمند توجه", ""])
    if averages:
        for average, metric, count in averages[:3]:
            lines.append(f"- **{LABELS[metric]}:** میانگین {average:.2f}/3 بر اساس {count} هفته")
    else:
        lines.append("- داده کافی برای مقایسه شاخص‌ها وجود ندارد.")
    lines.append("")

    lines.extend(["## نقاط نسبتاً پایدار", ""])
    if averages:
        for average, metric, count in reversed(averages[-3:]):
            lines.append(f"- **{LABELS[metric]}:** میانگین {average:.2f}/3 بر اساس {count} هفته")
    else:
        lines.append("- داده کافی وجود ندارد.")
    lines.append("")

    if safety_weeks:
        lines.extend(
            [
                "## بازبینی ایمنی/تجربه",
                "",
                "در هفته‌های زیر دست‌کم یک سیگنال قرمز ثبت شده است؛ این مورد با میانگین امتیاز پوشانده نمی‌شود:",
                *[f"- {week}" for week in safety_weeks],
                "",
            ]
        )

    if insufficient:
        lines.extend(
            [
                "## داده ناکافی",
                "",
                *[f"- {week}" for week in insufficient],
                "",
            ]
        )

    lines.extend(
        [
            "## کنترل انسانی و تحلیل کیفی",
            "",
            "این فایل فقط جمع‌بندی عددی است. تصمیم دوره باید با خواندن مشاهده‌ها، صدای ماهور، ظرفیت والدین و شرایط مدرسه انجام شود. برای گزارش روایی، از دستیار بخواهید فرم‌ها و گزارش‌های همین دوره را تحلیل و حداکثر سه اولویت بعدی را پیشنهاد کند.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    records = load_records()
    monthly_keys = sorted({key for _path, data in records if (key := period_key(data, "monthly"))})
    yearly_keys = sorted({key for _path, data in records if (key := period_key(data, "yearly"))})

    for kind, keys in (("monthly", monthly_keys), ("yearly", yearly_keys)):
        output_dir = REPORT_DIR / kind
        output_dir.mkdir(parents=True, exist_ok=True)
        for key in keys:
            (output_dir / f"{key}.md").write_text(aggregate(kind, key, records), encoding="utf-8")
            print(output_dir / f"{key}.md")


if __name__ == "__main__":
    main()

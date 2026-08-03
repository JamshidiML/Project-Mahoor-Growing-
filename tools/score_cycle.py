#!/usr/bin/env python3
"""Calculate Family Operating Score and generate a correction report.

Usage:
    python tools/score_cycle.py 07-data/weekly/2026-W32.json

The script scores family-system execution only. Child experience signals are
non-numeric safety/context gates and never contribute to a personality score.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WEIGHTS: dict[str, int] = {
    "father_connection": 10,
    "mother_connection": 10,
    "father_special_time": 8,
    "mother_special_time": 8,
    "parent_review": 8,
    "repair_after_conflict": 6,
    "listening_without_fixing": 8,
    "child_voice": 8,
    "low_pressure": 7,
    "warmth_predictability": 7,
    "sleep_routine": 5,
    "play_movement": 5,
    "social_opportunity": 5,
    "school_coordination": 5,
}

CATEGORY: dict[str, str] = {
    "father_connection": "اجرای والدین",
    "mother_connection": "اجرای والدین",
    "father_special_time": "اجرای والدین",
    "mother_special_time": "اجرای والدین",
    "parent_review": "اجرای والدین",
    "repair_after_conflict": "اجرای والدین",
    "listening_without_fixing": "کیفیت رابطه",
    "child_voice": "کیفیت رابطه",
    "low_pressure": "کیفیت رابطه",
    "warmth_predictability": "کیفیت رابطه",
    "sleep_routine": "محیط رشد",
    "play_movement": "محیط رشد",
    "social_opportunity": "محیط رشد",
    "school_coordination": "محیط رشد",
}

LABELS: dict[str, str] = {
    "father_connection": "اتصال بدون موبایل پدر",
    "mother_connection": "اتصال بدون موبایل مادر",
    "father_special_time": "وقت اختصاصی پدر–دختر",
    "mother_special_time": "وقت اختصاصی مادر–دختر",
    "parent_review": "جلسه هفتگی والدین",
    "repair_after_conflict": "ترمیم بعد از تنش",
    "listening_without_fixing": "شنیدن بدون نصیحت",
    "child_voice": "صدای ماهور و حق انتخاب",
    "low_pressure": "نبود فشار و مقایسه",
    "warmth_predictability": "گرمی و پیش‌بینی‌پذیری",
    "sleep_routine": "خواب و روتین",
    "play_movement": "بازی و حرکت",
    "social_opportunity": "فرصت اجتماعی کم‌فشار",
    "school_coordination": "هماهنگی لازم با مدرسه",
}

VALID_SIGNALS = {"GREEN", "AMBER", "RED", "UNKNOWN"}


@dataclass(frozen=True)
class MetricResult:
    key: str
    score: int
    weight: int
    weighted: float
    evidence: str


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Top-level JSON value must be an object.")
    return data


def validate_privacy(data: dict[str, Any]) -> list[str]:
    flags = data.get("privacy_check", {})
    warnings: list[str] = []
    for key in (
        "contains_child_audio",
        "contains_other_child_names",
        "contains_school_identifiers",
        "contains_medical_documents",
    ):
        if flags.get(key) is True:
            warnings.append(key)
    return warnings


def calculate(data: dict[str, Any]) -> tuple[float | None, float, list[MetricResult], list[str]]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise SystemExit("The 'metrics' field must be an object.")

    results: list[MetricResult] = []
    missing: list[str] = []

    for key, weight in WEIGHTS.items():
        raw = metrics.get(key, {})
        score = raw.get("score") if isinstance(raw, dict) else None
        evidence = str(raw.get("evidence", "")) if isinstance(raw, dict) else ""
        if score is None:
            missing.append(key)
            continue
        if not isinstance(score, int) or score not in {0, 1, 2, 3}:
            raise SystemExit(f"Metric '{key}' score must be 0, 1, 2, 3, or null.")
        results.append(
            MetricResult(
                key=key,
                score=score,
                weight=weight,
                weighted=(score / 3.0) * weight,
                evidence=evidence.strip(),
            )
        )

    coverage = len(results) / len(WEIGHTS)
    if coverage < 0.70:
        return None, coverage, results, missing

    available_weight = sum(item.weight for item in results)
    earned = sum(item.weighted for item in results)
    normalized = round((earned / available_weight) * 100, 1)
    return normalized, coverage, results, missing


def classify(score: float | None) -> str:
    if score is None:
        return "INSUFFICIENT_DATA"
    if score >= 85:
        return "GREEN"
    if score >= 70:
        return "YELLOW"
    if score >= 55:
        return "ORANGE"
    return "RED"


def child_signal_gate(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    raw = data.get("child_experience_signals", {})
    if not isinstance(raw, dict):
        return [], ["child_experience_signals"]
    red: list[str] = []
    invalid: list[str] = []
    for key, value in raw.items():
        normalized = str(value).upper()
        if normalized not in VALID_SIGNALS:
            invalid.append(key)
        elif normalized == "RED":
            red.append(key)
    return red, invalid


def select_focus(results: list[MetricResult], limit: int = 2) -> list[MetricResult]:
    return sorted(results, key=lambda item: (item.score, -item.weight))[:limit]


def recommendation(status: str, safety_review: bool) -> str:
    if safety_review:
        return "SAFETY_REVIEW — ابتدا نگرانی قرمز بررسی شود؛ افزایش فشار یا تمرین عملکردی ممنوع است."
    return {
        "GREEN": "CONTINUE — برنامه ادامه یابد و فقط یک بهبود کوچک انتخاب شود.",
        "YELLOW": "ADJUST — یک چرخه اصلاح هفت‌روزه با حداکثر دو تغییر اجرا شود.",
        "ORANGE": "ADJUST — دامنه برنامه کاهش و دو علت اصلی اصلاح شود.",
        "RED": "PAUSE — اهداف عملکردی متوقف و رابطه، فشار والدین و ایمنی بررسی شود.",
        "INSUFFICIENT_DATA": "COLLECT_DATA — فقط اطلاعات ضروری تکمیل شود؛ قضاوت نکنید.",
    }[status]


def build_report(
    data: dict[str, Any],
    score: float | None,
    coverage: float,
    results: list[MetricResult],
    missing: list[str],
    privacy_warnings: list[str],
    red_signals: list[str],
    invalid_signals: list[str],
) -> str:
    status = classify(score)
    safety_review = bool(red_signals)
    focus = select_focus(results)
    period_id = str(data.get("period_id", "unknown-period"))
    observations = data.get("observations", {})
    if not isinstance(observations, dict):
        observations = {}

    score_text = "نامعتبر — داده ناکافی" if score is None else f"{score:.1f}/100"
    lines = [
        f"# گزارش خودکار {period_id}",
        "",
        "## نتیجه",
        "",
        f"- **FOS:** {score_text}",
        f"- **پوشش داده:** {coverage * 100:.0f}%",
        f"- **وضعیت:** `{status}`",
        f"- **تصمیم:** {recommendation(status, safety_review)}",
        "",
    ]

    if privacy_warnings:
        lines.extend(
            [
                "## توقف حریم خصوصی",
                "",
                "این فایل دارای پرچم‌های حساس زیر است و نباید بدون پاک‌سازی ثبت یا پردازش شود:",
                *[f"- `{item}`" for item in privacy_warnings],
                "",
            ]
        )

    if red_signals or invalid_signals:
        lines.extend(["## گیت تجربه و ایمنی ماهور", ""])
        if red_signals:
            lines.append("وضعیت قرمز ثبت شده است:")
            lines.extend(f"- `{item}`" for item in red_signals)
        if invalid_signals:
            lines.append("مقادیر نامعتبر:")
            lines.extend(f"- `{item}`" for item in invalid_signals)
        lines.append("")

    lines.extend(["## امتیاز شاخص‌ها", "", "| حوزه | شاخص | نمره | سهم وزنی | شواهد |", "|---|---|---:|---:|---|"])
    for item in sorted(results, key=lambda result: list(WEIGHTS).index(result.key)):
        evidence = item.evidence.replace("|", "\\|") or "—"
        lines.append(
            f"| {CATEGORY[item.key]} | {LABELS[item.key]} | {item.score}/3 | {item.weighted:.1f}/{item.weight} | {evidence} |"
        )
    lines.append("")

    if missing:
        lines.extend(["## داده‌های نامشخص", "", *[f"- {LABELS[key]}" for key in missing], ""])

    lines.extend(["## تمرکز اصلاح هفت‌روزه", ""])
    if status == "GREEN" and focus:
        lines.append(f"- فقط یک بهبود کوچک: **{LABELS[focus[0].key]}**")
    elif focus:
        for item in focus:
            lines.append(f"- **{LABELS[item.key]}** — نمره {item.score}/3؛ یک تغییر کوچک، مشخص و قابل توقف تعریف شود.")
    else:
        lines.append("- ابتدا داده‌های ضروری تکمیل شود.")
    lines.append("")

    lines.extend(
        [
            "## مشاهده‌های کلیدی",
            "",
            f"- **لحظه مثبت:** {observations.get('one_positive_moment') or 'ثبت نشده'}",
            f"- **لحظه سخت:** {observations.get('one_difficult_moment') or 'ثبت نشده'}",
            f"- **چه چیزی کمک کرد:** {observations.get('what_helped') or 'ثبت نشده'}",
            f"- **چه چیزی فشار را بیشتر کرد:** {observations.get('what_increased_pressure') or 'ثبت نشده'}",
            f"- **صدای ماهور:** {observations.get('mahoor_voice') or 'ثبت نشده / تمایلی نداشت'}",
            f"- **ظرفیت والدین:** {observations.get('parent_capacity') or 'ثبت نشده'}",
            "",
            "## کنترل انسانی الزامی",
            "",
            "این گزارش باید توسط والدین مرور شود. رونویسی صوت، نمره‌گذاری و استنباط می‌تواند خطا داشته باشد. این خروجی تشخیص روان‌شناختی یا پزشکی نیست.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/score_cycle.py <weekly-input.json>")

    input_path = Path(sys.argv[1])
    data = load_json(input_path)
    privacy_warnings = validate_privacy(data)
    score, coverage, results, missing = calculate(data)
    red_signals, invalid_signals = child_signal_gate(data)

    report = build_report(
        data=data,
        score=score,
        coverage=coverage,
        results=results,
        missing=missing,
        privacy_warnings=privacy_warnings,
        red_signals=red_signals,
        invalid_signals=invalid_signals,
    )

    period_type = str(data.get("period_type", "weekly"))
    period_id = str(data.get("period_id", input_path.stem))
    output_path = Path("08-reports") / period_type / f"{period_id}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()

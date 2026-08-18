"""Aggregation and validation helpers for the recovery dashboard."""

from collections import defaultdict
from datetime import date, timedelta


RECOVERY_CATEGORIES = {
    "roads_repaired": "Roads repaired",
    "schools_reopened": "Schools reopened",
    "electricity_restored": "Electricity restored",
    "water_restored": "Water supply restored",
    "houses_rebuilt": "Houses rebuilt",
    "families_relocated": "Families relocated",
}


def recovery_summary(baselines, milestones):
    completed = defaultdict(int)
    for milestone in milestones:
        if milestone.is_verified:
            completed[(milestone.disaster_id, milestone.district, milestone.category)] += milestone.completed_count

    rows = []
    for baseline in baselines:
        value = completed[(baseline.disaster_id, baseline.district, baseline.category)]
        rows.append({
            "disaster_id": baseline.disaster_id,
            "disaster_title": baseline.disaster.title,
            "district": baseline.district,
            "category": baseline.category,
            "category_label": RECOVERY_CATEGORIES[baseline.category],
            "completed": value,
            "total": baseline.estimated_total,
            "percentage": min(100.0, value / baseline.estimated_total * 100) if baseline.estimated_total else 0.0,
        })
    return rows


def weekly_trend(milestones):
    weekly = defaultdict(int)
    for milestone in milestones:
        if not milestone.is_verified:
            continue
        week = milestone.milestone_date - timedelta(days=milestone.milestone_date.weekday())
        weekly[week] += milestone.completed_count

    running = 0
    labels, values = [], []
    for week, count in sorted(weekly.items()):
        running += count
        labels.append(week.isoformat())
        values.append(running)
    return {"labels": labels, "values": values}

from pathlib import Path

import pandas as pd
import pytest

from common import stats
from common.constants import PROCESSED_DIR, REPORTS_DIR

FINDINGS = Path(REPORTS_DIR / "findings.md")


@pytest.fixture(scope="module")
def text():
    return FINDINGS.read_text()


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(PROCESSED_DIR / "panel.csv")


def test_findings_state_the_question_1_answer_from_the_data(text, panel):
    summary = stats.change_summary(stats.gender_gap_by_year(panel))
    winner = stats.largest_change(summary["change"])
    assert f"**{winner}**" in text
    assert f"{summary.loc[winner, 'change']:+.2f} years" in text


def test_findings_state_the_question_2_answer_from_the_data(text, panel):
    summary = stats.change_summary(stats.spread_by_year(panel, "standard_deviation"))
    winner = stats.largest_change(summary["change"])
    assert f"**{winner}**" in text
    assert f"{summary.loc[winner, 'change']:+.2f}" in text


def test_findings_state_the_question_3_answer_from_the_data(text, panel):
    correlations = stats.country_correlations(panel)
    strongest = correlations.iloc[0]
    weakest = correlations.iloc[-1]
    assert f"**{strongest['country']}** ({strongest['pearson']:+.4f})" in text
    assert f"**{weakest['country']}** ({weakest['pearson']:+.4f})" in text


def test_findings_show_charts_that_exist(text):
    for name in ("income_line_chart", "world_map", "ranked_chart", "sankey", "moves_heatmap"):
        assert f"](figures/{name}.png)" in text
        assert (REPORTS_DIR / "figures" / f"{name}.png").exists()

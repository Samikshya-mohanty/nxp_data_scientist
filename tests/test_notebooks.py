import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

NOTEBOOK = Path(__file__).parents[1] / "notebooks" / "01_statistics.py"


def load_app():
    spec = importlib.util.spec_from_file_location("statistics_notebook", NOTEBOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


def test_statistics_notebook_runs_as_a_script():
    result = subprocess.run([sys.executable, str(NOTEBOOK)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "definition, winner",
    [
        ("all countries", "Upper middle income"),
        ("only countries with both years", "Upper middle income"),
        ("population weights", "Lower middle income"),
        ("1960-62 to 2017-19 averages", "Low income"),
    ],
)
def test_question_1_answer_follows_the_chosen_definition(definition, winner):
    _, defs = load_app().run(defs={"q1_definition": SimpleNamespace(choice=definition)})
    assert defs["q1_winner"] == winner


@pytest.mark.parametrize(
    "measure, winner",
    [
        ("standard deviation", "Upper middle income"),
        ("IQR", "Upper middle income"),
        ("range", "Upper middle income"),
        ("coefficient of variation", "Low income"),
    ],
)
def test_question_2_answer_follows_the_chosen_measure(measure, winner):
    _, defs = load_app().run(defs={"q2_measure": SimpleNamespace(choice=measure)})
    assert defs["q2_winner"] == winner


def test_question_3_names_the_strongest_and_weakest_countries():
    _, defs = load_app().run()
    assert defs["q3_strongest"] == "India"
    assert defs["q3_weakest"] == "Belarus"

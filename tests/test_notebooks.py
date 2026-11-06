import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

NOTEBOOKS = Path(__file__).parents[1] / "notebooks"


def load_app(name):
    spec = importlib.util.spec_from_file_location(name, NOTEBOOKS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


@pytest.mark.parametrize("name", ["01_statistics", "02_charts"])
def test_notebook_runs_as_a_script(name):
    result = subprocess.run([sys.executable, str(NOTEBOOKS / f"{name}.py")], capture_output=True, text=True)
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
    _, defs = load_app("01_statistics").run(defs={"q1_definition": SimpleNamespace(choice=definition)})
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
    _, defs = load_app("01_statistics").run(defs={"q2_measure": SimpleNamespace(choice=measure)})
    assert defs["q2_winner"] == winner


def test_question_3_names_the_strongest_and_weakest_countries():
    _, defs = load_app("01_statistics").run()
    assert defs["q3_strongest"] == "India"
    assert defs["q3_weakest"] == "Belarus"


def test_charts_notebook_lists_the_countries_in_a_chosen_move():
    _, defs = load_app("02_charts").run(
        defs={
            "move_from": SimpleNamespace(value="Low life expectancy"),
            "move_to": SimpleNamespace(value="Very high life expectancy"),
        }
    )
    assert set(defs["movers"]["country"]) == {"United Arab Emirates", "Bahrain"}


def test_charts_notebook_follows_the_bucket_count():
    _, defs = load_app("02_charts").run(defs={"bucket_count": SimpleNamespace(amount=3.0)})
    assert defs["labels"] == ("Bucket 1 (lowest)", "Bucket 2", "Bucket 3 (highest)")
    assert len(defs["moves"]) == 215

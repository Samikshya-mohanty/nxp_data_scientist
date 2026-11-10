from zlib import crc32

from plotly.colors import sample_colorscale

from common.constants import INCOME_GROUPS

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e6e5e1"
NO_DATA = "#d9d8d3"
BAND = "#efeeea"
BAR = "#2a78d6"

INCOME_COLORS = dict(zip(INCOME_GROUPS, ("#86b6ef", "#3987e5", "#1c5cab", "#104281")))
BUCKET_RAMP = ["#b7d3f6", "#86b6ef", "#3987e5", "#1c5cab", "#104281"]
SEQUENTIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"]
DIVERGING = ["#eb6834", "#d9d8d3", "#1c5cab"]
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
REGION_COLORS = dict(
    zip(
        [
            "East Asia & Pacific",
            "Europe & Central Asia",
            "Latin America & Caribbean",
            "Middle East, North Africa, Afghanistan & Pakistan",
            "North America",
            "South Asia",
            "Sub-Saharan Africa",
        ],
        CATEGORICAL,
    )
)


def series_color(name, group_by):
    if group_by == "Income group":
        return INCOME_COLORS[name]
    if group_by == "Region":
        return REGION_COLORS[name]
    return CATEGORICAL[crc32(name.encode()) % len(CATEGORICAL)]


def bucket_colors(labels):
    return dict(zip(labels, sample_colorscale(BUCKET_RAMP, len(labels))))


def apply_theme(figure, title, subtitle=""):
    figure.update_layout(
        title={
            "text": f"{title}<br><span style='font-size:13px;color:{MUTED}'>{subtitle}</span>",
            "x": 0.01,
            "xanchor": "left",
            "font": {"size": 18, "color": TEXT},
        },
        font={"family": "Inter, Helvetica, Arial, sans-serif", "color": TEXT, "size": 13},
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
    )
    return figure

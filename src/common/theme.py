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

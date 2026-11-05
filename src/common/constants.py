from pathlib import Path

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
PROCESSED_DIR = RAW_DIR.parent / "processed"
REPORTS_DIR = RAW_DIR.parents[1] / "reports"
INCOME_GROUPS = ("Low income", "Lower middle income", "Upper middle income", "High income")
INDICATORS = {
    "SP.DYN.LE00.IN": "life_exp",
    "SP.DYN.LE00.MA.IN": "life_exp_male",
    "SP.DYN.LE00.FE.IN": "life_exp_female",
    "SP.DYN.CDRT.IN": "death_rate",
    "SP.DYN.TFRT.IN": "fertility",
}

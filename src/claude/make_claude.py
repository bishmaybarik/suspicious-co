"""Run Claude's blind-discovery pipeline end to end.

Every table and figure referenced in research/claude/ is regenerated from the
immutable input by running this file. Scripts are ordered by dependency.
"""

import subprocess
import sys
from pathlib import Path

script_path = Path(__file__).resolve().parent

# ordered because 03 writes entity_enriched.parquet, which 04 to 07 consume
script_list = [
    "01_audit_rows.py",
    "02_build_hierarchy.py",
    "03_analyse_hierarchy.py",
    "04_analyse_jurisdiction.py",
    "05_analyse_coverage_financials.py",
    "06_audit_uin_structure.py",
    "07_make_figures.py",
]

for script_name in script_list:
    # fail loudly on the first broken step rather than silently continuing
    print(f"\n=== running {script_name} ===", flush=True)
    subprocess.run([sys.executable, str(script_path / script_name)], check=True)

print("\nclaude pipeline complete")

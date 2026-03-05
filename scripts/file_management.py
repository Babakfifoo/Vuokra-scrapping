# %%
import os
from pathlib import Path

folder = Path("../app/data/json")  # change to your folder path
# %%

for f in folder.glob("2026-02--*"):
    new_name = f.name.replace("2026-02--", "2026-02-21-", 1)
    f.rename(f.parent / new_name)
# %%
for f in folder.iterdir():
    if f.is_file() and len(f.name) >= 11 and f.name[10] != "-":
        new_name = f.name[:10] + "-" + f.name[10:]
        f.rename(f.parent / new_name)
# %%
        
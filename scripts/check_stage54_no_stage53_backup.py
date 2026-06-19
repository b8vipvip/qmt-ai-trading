from pathlib import Path

bad = list(Path("scripts").glob("validate_stage53.ps1.bak_*"))
bad += list(Path("scripts").glob("validate_stage53.ps1.bak_stage54fix_*"))

if bad:
    print("Stage53 backup files still exist:")
    for p in bad:
        print("-", p)
    raise SystemExit(1)

print("Stage53 backup files cleaned.")

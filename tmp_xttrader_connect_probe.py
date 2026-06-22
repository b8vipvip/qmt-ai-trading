import random
from pathlib import Path

from xtquant.xttrader import XtQuantTrader

paths = [
    r"D:\国金证券QMT交易端\userdata_mini",
    r"D:\国金证券QMT交易端\bin.x64\..\userdata_mini",
]

for p in paths:
    path = str(Path(p).resolve())
    print("\n=== try path ===")
    print(path)
    print("exists:", Path(path).exists())

    try:
        session_id = random.randint(100000, 999999)
        trader = XtQuantTrader(path, session_id)
        trader.start()
        result = trader.connect()
        print("connect_result:", result)
    except Exception as e:
        print("ERROR:", repr(e))
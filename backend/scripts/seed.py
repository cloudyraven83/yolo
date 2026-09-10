"""初始化/重置种子数据：python scripts/seed.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.db import Base, engine  # noqa: E402
from app.core.seed import DEFAULT_ADMIN, auto_seed  # noqa: E402

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    result = auto_seed()
    print("种子数据初始化完成:", result)
    print(f"管理员账号: {DEFAULT_ADMIN[0]} / {DEFAULT_ADMIN[1]}（首次登录后建议修改）")

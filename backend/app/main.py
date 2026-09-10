from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import FRONTEND_DIST
from .core.db import Base, engine
from .core.seed import auto_seed, load_drinks_config
from .core.runtime import runtime
from .routers import admin, camera, demo, inventory, model, records, session, stats
from engine.detector import manager as provider_manager
from engine.simulated import SimulatedProvider
from engine.yolo_camera import YoloCameraProvider

app = FastAPI(title="饮料种类识别与无人售货机", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# 建表 + 种子数据（幂等）
Base.metadata.create_all(engine)
_seed_result = auto_seed()

# 注册识别通道（模拟通道默认；YOLO 通道懒加载，避免启动时联网下载阻塞）
_drinks_cfg = load_drinks_config()
_sim = SimulatedProvider()
_sim.load(_drinks_cfg)
_yolo = YoloCameraProvider()
_yolo.cfg = _drinks_cfg  # 注入配置，权重在切换到该通道或首次检测时才加载
provider_manager.register(_sim)
provider_manager.register(_yolo)
runtime.provider_name = "simulated"

for r in (admin.router, camera.router, demo.router, inventory.router,
          model.router, records.router, session.router, stats.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "seed": _seed_result,
        "provider": runtime.provider_name,
    }


# 前端静态托管（同源部署，避免本地跨域）+ SPA history 路由回退
if FRONTEND_DIST.exists():
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        file = FRONTEND_DIST / full_path
        if full_path and file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")

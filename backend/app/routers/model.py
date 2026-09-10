from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.runtime import runtime
from engine.detector import manager as provider_manager

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/status")
def status():
    return {"current": runtime.provider_name, "providers": provider_manager.status()}


class SwitchBody(BaseModel):
    provider: str


@router.post("/switch")
def switch(body: SwitchBody):
    if runtime.session_id is not None:
        raise HTTPException(400, "识别会话进行中，请先关门再切换识别通道")
    try:
        provider = provider_manager.get(body.provider)
    except KeyError:
        raise HTTPException(400, f"未知识别通道: {body.provider}")
    provider.load()  # 触发加载（YOLO 通道首次切换时加载权重，可能耗时）
    runtime.provider_name = body.provider
    return {"current": runtime.provider_name, "provider": provider.status()}

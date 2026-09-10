"""识别引擎 Provider 抽象与工厂。

阶段一双通道：
- SimulatedProvider（默认）：确定性演示事件，验收口径。
- YoloCameraProvider：OpenCV + ultralytics 预训练权重，演示真实链路。

阶段二自定义权重训练完成后，仅需在 configs/drinks.yaml 中把
model.weights 指向 models/best.pt，并补充 label->商品 映射即可，
上层业务（会话/结算/库存/预警/统计）零改动。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class Detection:
    label: str
    confidence: float
    region: str = ""  # "x1,y1,x2,y2"
    ts: datetime = field(default_factory=datetime.now)


class DetectionProvider(ABC):
    name = "base"

    @abstractmethod
    def load(self, cfg: dict) -> None:
        ...

    @abstractmethod
    def detect(self, frame) -> list:
        ...

    @abstractmethod
    def status(self) -> dict:
        ...


class ProviderManager:
    """识别通道工厂/切换器（进程内单例）。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._providers = {}

    def register(self, provider: DetectionProvider):
        self._providers[provider.name] = provider

    def get(self, name: str) -> DetectionProvider:
        if name not in self._providers:
            raise KeyError(f"未知识别通道: {name}")
        return self._providers[name]

    def status(self) -> dict:
        return {name: p.status() for name, p in self._providers.items()}


manager = ProviderManager()

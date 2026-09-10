"""YOLO 摄像头识别通道（阶段一：预训练权重，仅演示链路）。

ultralytics 为懒加载依赖：未安装时通道不可用但不影响模拟通道与整体服务。
自定义权重就绪后，仅需修改 configs/drinks.yaml 的 model.weights 与
label_mapping（COCO/自定义类别名 -> 商品名），业务层无需改动。
"""

from .detector import Detection, DetectionProvider


class YoloCameraProvider(DetectionProvider):
    name = "yolo"

    def __init__(self):
        self.model = None
        self.err = None
        self.conf = 0.25
        self.frame_no = 0
        self.label_mapping = {}  # 模型类别名 -> 商品名（阶段二训练后配置）
        self.cfg = None          # 注册时由应用注入配置
        self._attempted = False  # 防止加载失败时逐帧重试

    def load(self, cfg: dict = None) -> None:
        cfg = cfg if cfg is not None else (self.cfg or {})
        self.cfg = cfg
        if self._attempted and self.model is not None:
            return  # 已成功加载，幂等
        self._attempted = True
        model_cfg = (cfg or {}).get("model", {})
        self.conf = float(model_cfg.get("conf_threshold", 0.25))
        self.label_mapping = model_cfg.get("label_mapping", {}) or {}
        weights = model_cfg.get("weights", "yolov8n.pt")
        try:
            from ultralytics import YOLO  # 懒加载，缺依赖时优雅降级
            self.model = YOLO(weights)
            self.err = None
        except Exception as e:  # noqa: BLE001
            self.model = None
            self.err = f"YOLO 通道不可用: {e}"

    def detect(self, frame) -> list:
        if self.model is None and not self._attempted:
            self.load()  # 懒加载：首次检测时加载权重
        if self.model is None or frame is None:
            return []
        self.frame_no += 1
        try:
            res = self.model.predict(frame, conf=self.conf, verbose=False)[0]
        except Exception:  # noqa: BLE001
            return []
        out = []
        names = res.names or {}
        for b in res.boxes:
            raw = names.get(int(b.cls[0]), str(int(b.cls[0])))
            label = self.label_mapping.get(raw, raw)
            box = b.xyxy[0].tolist()
            out.append(
                Detection(
                    label=label,
                    confidence=round(float(b.conf[0]), 3),
                    region=",".join(str(int(v)) for v in box),
                )
            )
        return out

    def status(self) -> dict:
        return {
            "name": self.name,
            "available": self.model is not None,
            "loaded": self._attempted,
            "error": self.err,
            "desc": "YOLO 摄像头通道（预训练权重，仅演示链路，不做品牌级判定）",
        }

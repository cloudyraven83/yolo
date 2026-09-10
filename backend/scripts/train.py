"""YOLO 自定义数据集训练骨架（阶段一预留，不执行训练）。

阶段二使用步骤：
  1. 将标注好的数据集放入 data/drinks/（images/labels + data.yaml）
  2. 在 configs/drinks.yaml 中配置 label_mapping（模型类别名 -> 商品名）
  3. 运行: python scripts/train.py --epochs 100 --imgsz 640
  4. 训练产物 best.pt 放入 models/，并将 configs/drinks.yaml 的
     model.weights 改为 models/best.pt，重启服务即切换自定义权重，
     上层业务（会话/结算/库存/预警/统计）零改动。

用法: python scripts/train.py [--data data/drinks/data.yaml] [--epochs 100]
                              [--imgsz 640] [--base yolov8n.pt] [--dry-run]
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


def main():
    ap = argparse.ArgumentParser(description="YOLO 饮料识别模型训练（阶段二）")
    ap.add_argument("--data", default=str(BACKEND_DIR / "data" / "drinks" / "data.yaml"))
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--base", default="yolov8n.pt", help="预训练基础权重")
    ap.add_argument("--dry-run", action="store_true", help="只校验配置与数据集，不训练")
    args = ap.parse_args()

    data_yaml = Path(args.data)
    if not data_yaml.exists():
        print(f"[退出] 数据集配置不存在: {data_yaml}")
        print("请先按 data/drinks/data.yaml 中的目录约定准备标注数据。")
        sys.exit(1)

    try:
        import yaml
        cfg = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
        names = cfg.get("names") or []
    except Exception as e:  # noqa: BLE001
        print(f"[退出] 数据集配置解析失败: {e}")
        sys.exit(1)

    if not names:
        print("[提示] data.yaml 的 names 为空：尚未配置饮料类别（阶段一正常）。")
    if args.dry_run:
        print(f"[dry-run] data={data_yaml} epochs={args.epochs} imgsz={args.imgsz} base={args.base}")
        print("[dry-run] 配置校验完成。")
        return

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[退出] 未安装 ultralytics，请先 pip install ultralytics")
        sys.exit(1)

    model = YOLO(args.base)
    model.train(data=str(data_yaml), epochs=args.epochs, imgsz=args.imgsz,
                project=str(BACKEND_DIR / "models"), name="drinks")
    print("训练完成。请将 runs/drinks 下的 best.pt 复制到 models/，")
    print("并将 configs/drinks.yaml 的 model.weights 改为 models/best.pt。")


if __name__ == "__main__":
    main()

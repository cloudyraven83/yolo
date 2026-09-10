# 饮料种类识别与无人售货机（第一阶段）

基于 YOLO 的货架饮料识别 + 自助结算 + 后台管理系统。模拟真实售货机：
**开门（开始识别）→ 取走饮料 → 关门（自动结算）→ 模拟支付**；
货道低库存/售空自动向管理员后台推送补货预警；后台提供近 7 天销售额曲线、品类销售占比等运营视图。

- 后端：FastAPI + SQLite + OpenCV + ultralytics（YOLO，懒加载）
- 前端：Vue3 + Vite + ECharts（由后端同源托管，本地网页访问）
- 识别双通道：**模拟识别（默认，确定性演示）** / **YOLO 摄像头（预训练权重，演示链路）**，可页面切换
- 阶段一不训练模型；训练接口已预留（见"阶段二"）

## 一、快速启动（Windows 一键）

前置：已安装 Anaconda（含 conda 环境 `py3.10`）与 Node.js。

```
双击 start.bat        # 一键启动
双击 stop.bat         # 一键关闭（也可在启动窗口按 Ctrl+C）
```

启动后访问 <http://127.0.0.1:8000>（局域网可用本机 IP 访问）。
管理员账号：`admin / admin123`（登录入口在页面右上角）。

### 手动启动（调试用）

```bash
conda activate py3.10
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
cd backend && python scripts/seed.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

前端联调开发：后端启动后另开终端 `cd frontend && npm run dev`，访问 <http://127.0.0.1:5173>（已配置 /api 代理）。

## 二、演示剧本（对应验收 S1–S5）

1. **模拟结算**：操作台点"开门·开始识别"→ 演示场景区选"可口可乐 ×2、冰红茶 ×1"加入并注入 → 点"关门·结束识别"→ 结算单金额 ¥10.00 → "模拟支付"。
2. **补货闭环**：注入拿走数量超过库存的场景 → 关门后出现"售空/低库存"预警 → 管理员登录后台"预警与记录"查看 → "库存补货"页面对该货道补货 → 预警自动关闭。
3. **后台图表**：完成多笔交易后，"运营概览"中近 7 天销售额折线、品类占比饼图随之变化。
4. **摄像头通道**：操作台点"切换"至 YOLO 通道（首次切换需加载权重），预览区显示摄像头画面并叠加检测框，识别日志持续写入（不计入成交）；无摄像头时显示占位画面，不影响其他功能。
5. **权限与健壮性**：未登录访问后台接口返回 401；会话进行中重复开门/切换通道被拒绝；拿走数量超库存时按实际库存结算并提示。

> YOLO 真跑通道依赖较大（含 torch 约 2GB），按需安装：
> `pip install -r backend/requirements-yolo.txt`。默认模拟通道无需安装。
> 首次切换 YOLO 通道会自动下载 yolov8n.pt 预训练权重（约 6MB）。

## 三、目录结构

```
start.bat                       # 一键启动（Windows）
task.md                         # 项目方案与开发大纲（评审稿）
backend/
  app/main.py                   # FastAPI 入口（API + 前端静态托管 + SPA 回退）
  app/core/                     # 配置 / 数据库 / 鉴权(JWT) / 运行状态 / 种子数据
  app/models.py                 # SQLite 表模型（商品/货道/会话/明细/识别日志/补货/预警/管理员）
  app/routers/                  # camera session demo inventory admin stats model records
  app/services/                 # 会话结算与库存预警 / 运营统计
  engine/                       # 识别引擎：Provider 抽象 + 模拟通道 + YOLO 通道 + 摄像头管理
  configs/drinks.yaml           # 商品/货道/单价/阈值 + 模型权重与类别映射（阶段二改这里）
  scripts/seed.py               # 初始化种子数据（管理员 + 8 种饮料）
  scripts/smoke_test.py         # 端到端冒烟测试（21 项验收断言）
  scripts/train.py              # 训练骨架（阶段二使用）
  data/drinks/data.yaml         # YOLO 数据集规范占位（阶段二填充）
  models/                       # 权重产物目录（阶段二放 best.pt）
frontend/
  src/pages/                    # 顾客操作台 / 管理员登录 / 运营概览 / 库存补货 / 预警与记录
```

## 四、核心口径

- **库存唯一事实源**：成交即扣货道库存，禁止负库存（超出按实际库存结算并提示）。
- **补货预警**：关门结算后 `stock < threshold` 自动生成预警；补货恢复到阈值以上自动关闭。
- **识别准确率（演示口径）**：成交识别事件 ÷ 全部识别事件；阶段二接入真值后切换正式口径。
- **单机单会话**：同一时刻仅允许一个开门会话，重复开门/会话中切换通道被拒绝。

## 五、阶段二（训练自定义模型）

1. 采集并标注饮料图片，放入 `backend/data/drinks/`（images/labels + 补全 data.yaml 的 names）。
2. `cd backend && python scripts/train.py --epochs 100`（先 `--dry-run` 校验配置）。
3. 将训练产物 `best.pt` 放入 `backend/models/`，把 `configs/drinks.yaml` 的
   `model.weights` 改为 `models/best.pt`，并在 `label_mapping` 中配置"类别名→商品名"。
4. 重启服务即切换自定义权重，业务层零改动。

## 六、常见问题

- **摄像头打不开**：确认未被其他程序占用；可用环境变量 `set CAMERA_ID=1` 换摄像头后重启；无摄像头时系统自动使用占位画面。
- **切换 YOLO 通道失败**：确认已安装 `requirements-yolo.txt`；权重下载需联网（github）。
- **重置演示数据**：停止服务后删除 `backend/data/app.db`，重启自动重建种子数据。
- **冒烟测试**：服务运行中执行 `python backend/scripts/smoke_test.py`（21 项断言）。

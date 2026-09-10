"""全局运行状态：单机单会话 + 当前识别通道。"""

import threading


class Runtime:
    def __init__(self):
        self.lock = threading.Lock()
        self.session_id = None      # 当前 open 会话 id
        self.provider_name = "simulated"  # simulated / yolo
        self.last_log_ts = 0.0      # 摄像头通道识别日志节流时间戳


runtime = Runtime()

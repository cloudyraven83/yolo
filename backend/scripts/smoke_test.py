"""端到端冒烟测试：模拟通道全链路验收（S1-S5）。

前置：服务已在 http://127.0.0.1:8000 运行。
用法: python scripts/smoke_test.py
"""

import sys

import requests

BASE = "http://127.0.0.1:8000/api"
FAILED = []


def check(name, cond, detail=""):
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}" + (f" -> {detail}" if detail else ""))
    if not cond:
        FAILED.append(name)


def main():
    r = requests.get(f"{BASE}/health")
    check("health", r.status_code == 200 and r.json().get("ok"))

    products = requests.get(f"{BASE}/products").json()
    check("products>=8", len(products) >= 8, f"{len(products)} 个商品")
    pid = {p["name"]: p["id"] for p in products}

    # 先登录，记录可乐初始库存（断言用前后差值，可重复运行）
    login = requests.post(f"{BASE}/admin/login",
                          json={"username": "admin", "password": "admin123"})
    check("admin/login", login.status_code == 200)
    token = login.json()["token"]
    H = {"Authorization": f"Bearer {token}"}
    cola_stock0 = next(x["stock"] for x in requests.get(f"{BASE}/inventory", headers=H).json()
                       if x["name"] == "可口可乐")

    # S1 模拟结算：拿走 2 瓶可口可乐 + 1 瓶冰红茶
    s = requests.post(f"{BASE}/session/start").json()
    check("session/start", s.get("status") == "open", str(s))
    sid = s["session_id"]

    inj = requests.post(f"{BASE}/demo/scenario", json={"items": [
        {"product_id": pid["可口可乐"], "qty": 2},
        {"product_id": pid["冰红茶"], "qty": 1},
    ]}).json()
    check("demo/scenario", inj.get("injected_events") == 3, str(inj))

    settle = requests.post(f"{BASE}/session/stop").json()
    expect = round(2 * 3.5 + 1 * 3.0, 2)
    check("session/stop 金额", settle.get("total_amount") == expect,
          f"total={settle.get('total_amount')} expect={expect} warn={settle.get('warnings')}")

    pay = requests.post(f"{BASE}/session/{sid}/pay").json()
    check("session/pay", pay.get("status") == "paid")

    inv = requests.get(f"{BASE}/inventory", headers=H).json()
    cola = next(x for x in inv if x["name"] == "可口可乐")
    check("库存扣减(可乐-2)", cola["stock"] == cola_stock0 - 2,
          f"{cola_stock0} -> {cola['stock']}")

    # 无 token 拒绝（S5）
    r = requests.get(f"{BASE}/inventory")
    check("未登录拒绝(401)", r.status_code == 401)

    # S2 预警闭环：清空可乐触发预警 -> 补货恢复
    s2 = requests.post(f"{BASE}/session/start").json()["session_id"]
    requests.post(f"{BASE}/demo/scenario", json={"items": [
        {"product_id": pid["可口可乐"], "qty": 10}]})
    settle2 = requests.post(f"{BASE}/session/stop").json()
    check("负库存保护", any("库存仅" in w for w in settle2.get("warnings", [])),
          str(settle2.get("warnings")))
    requests.post(f"{BASE}/session/{s2}/pay")

    alerts = requests.get(f"{BASE}/alerts", headers=H).json()
    open_alerts = [a for a in alerts if a["status"] == "open" and a["product"] == "可口可乐"]
    check("售空预警生成", len(open_alerts) >= 1,
          open_alerts[0]["message"] if open_alerts else "无预警")

    lane_id = next(x["lane_id"] for x in inv if x["name"] == "可口可乐")
    rk = requests.post(f"{BASE}/restock", headers=H,
                       json={"lane_id": lane_id, "quantity": 8}).json()
    check("补货登记", rk.get("ok") and rk.get("stock") > 0, str(rk))
    alerts2 = requests.get(f"{BASE}/alerts", headers=H).json()
    check("补货后预警自动关闭",
          all(a["status"] == "resolved" for a in alerts2 if a["product"] == "可口可乐"))

    # S3 统计
    ov = requests.get(f"{BASE}/stats/overview", headers=H).json()
    check("stats/overview", ov.get("total_orders", 0) >= 2 and ov.get("total_sales", 0) > 0,
          str(ov))
    trend = requests.get(f"{BASE}/stats/trend?days=7", headers=H).json()
    check("stats/trend 7天", len(trend) == 7 and trend[-1]["amount"] > 0, str(trend[-1]))
    cat = requests.get(f"{BASE}/stats/category", headers=H).json()
    check("stats/category", any(c["name"] == "可口可乐" for c in cat), str(cat))

    # 会话与识别日志
    sess = requests.get(f"{BASE}/sessions", headers=H).json()
    check("sessions 列表", len(sess) >= 2)
    detail = requests.get(f"{BASE}/sessions/{sid}", headers=H).json()
    check("会话明细+识别日志",
          len(detail.get("items", [])) == 2 and len(detail.get("logs", [])) == 3,
          f"items={len(detail.get('items', []))} logs={len(detail.get('logs', []))}")

    # S4 识别通道状态与切换保护
    ms = requests.get(f"{BASE}/model/status").json()
    check("model/status", ms.get("current") == "simulated", str(ms.get("providers", {}).keys()))
    requests.post(f"{BASE}/session/start")
    r = requests.post(f"{BASE}/model/switch", json={"provider": "yolo"})
    check("会话中禁止切换通道(400)", r.status_code == 400)
    requests.post(f"{BASE}/session/stop")

    # S5 摄像头状态（无摄像头也应正常返回）
    cam = requests.get(f"{BASE}/camera/status").json()
    check("camera/status 兜底", "camera_available" in cam, str(cam))

    print("\n====", "全部通过" if not FAILED else f"失败 {len(FAILED)} 项: {FAILED}")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()

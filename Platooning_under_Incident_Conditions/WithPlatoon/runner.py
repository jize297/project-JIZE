#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runner.py – 控制 SUMO 仿真执行至指定时间，并在 0–3600 s
            动态封闭多条车道，结束后恢复
"""
# 27398
import os
import sys
import logging

# ────────────────────── 基础配置 ──────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

if "SUMO_HOME" not in os.environ:
    sys.exit("❌ 请先设置 SUMO_HOME 环境变量")
tools = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(tools)

import traci
from traci.exceptions import FatalTraCIError
import sumolib
import simpla
from simpla import SimplaException

USE_GUI    = 'nogui' not in sys.argv
SUMO_BIN   = 'sumo-gui' if USE_GUI else 'sumo'
SUMO_CFG   = 'M50_simulation.sumocfg'
NET_FILE   = 'M50network.net.xml.gz'
SIMPLA_CFG = 'simpla.cfg.xml'
END_TIME   = 28800        # 仿真结束 (秒)

# ─── 车道封闭参数 ──────────────────────────────────────────
CLOSED_LANES = [
    "106130759-AddedOffRampEdge_3",
    "328393125-AddedOnRampEdge_3",
    "615002705#0_1",
    "615002705#0_3",
]
BLOCK_BEGIN  = 25200          # 封闭开始时间 (s)
BLOCK_END    = 27900      # 封闭结束时间 (s)
DISALLOWED   = ["private", "passenger", "truck", "bus", "taxi", "coach",
                "delivery", "trailer", "motorcycle", "evehicle", "vip",
                "army", "hov", "custom1", "custom2"]

# ────────────────────── 启动 SUMO ‑ Simpla ─────────────
sumo_cmd = [
    sumolib.checkBinary(SUMO_BIN),
    "-c", SUMO_CFG,
    "--net-file", NET_FILE,
    "--step-length", "0.2",
    "--xml-validation.routes", "never",
]
logging.info("🚦 启动 SUMO: %s", " ".join(sumo_cmd))
try:
    traci.start(sumo_cmd)
except Exception as e:
    logging.error("❌ 无法启动 SUMO: %s", e)
    sys.exit(1)

try:
    logging.info("🔧 加载 Simpla 配置: %s", SIMPLA_CFG)
    simpla.load(SIMPLA_CFG)
except SimplaException as e:
    logging.error("❌ 加载 Simpla 失败: %s", e)
    traci.close()
    sys.exit(1)

# ────────────────────── 主循环 ─────────────────────────
original_allowed = {}   # {lane_id: [classes…]}
lanes_closed     = set()

try:
    while traci.simulation.getTime() < END_TIME:
        sim_time = traci.simulation.getTime()

        # 首次遇到某条 lane 时，记录其原 allowed 列表
        for lane in CLOSED_LANES:
            if lane not in original_allowed:
                original_allowed[lane] = traci.lane.getAllowed(lane)

        # 到达封闭起点：统一封闭
        if sim_time >= BLOCK_BEGIN and not lanes_closed:
            for lane in CLOSED_LANES:
                traci.lane.setDisallowed(lane, DISALLOWED)
                logging.info("⛔ %.1f s: 封闭 %s", sim_time, lane)
            lanes_closed.update(CLOSED_LANES)

        # 到了解封时刻：统一恢复
        if sim_time >= BLOCK_END and lanes_closed:
            for lane in CLOSED_LANES:
                traci.lane.setAllowed(lane, original_allowed[lane])
                logging.info("✅ %.1f s: 解封 %s", sim_time, lane)
            lanes_closed.clear()

        traci.simulationStep()  # 推进一步
except FatalTraCIError as e:
    logging.warning("⚠️ TraCI 连接被重置（SUMO 可能已退出）: %s", e)
except Exception as e:
    logging.error("❌ 仿真运行时出错: %s", e)
finally:
    logging.info("🛑 仿真结束，实际时间: %.2f s",
                 traci.simulation.getTime())
    traci.close()

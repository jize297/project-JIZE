#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runner.py - 整合 SUMO、Simpla 与 TraCI 的主程序，支持随机碰撞和日志统计
"""

import os
import sys
import logging
import random

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# 检查环境变量
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    if tools not in sys.path:
        sys.path.append(tools)
else:
    sys.exit("请设置环境变量 SUMO_HOME")

import traci
from traci.exceptions import FatalTraCIError
import sumolib
import simpla
from simpla import SimplaException

# 是否启用 GUI
binary = "sumo-gui"
if "nogui" in sys.argv:
    binary = "sumo"

# 配置文件路径
sumo_cfg = "M50_simulation.sumocfg"
simpla_cfg = "simpla.cfg.xml"

# SUMO 启动命令
sumo_cmd = [
    sumolib.checkBinary(binary),
    "-c", sumo_cfg,
    "--step-length", "0.5",
    "--fcd-output", "fcd.xml",
    "--fcd-output.max-leader-distance", "100",
    "--xml-validation.routes", "never",
    "--verbose", "true",
    "--collision.action", "warn"  # 保留碰撞车辆
]

logging.info("Starting SUMO with command: %s", " ".join(sumo_cmd))
try:
    traci.start(sumo_cmd)
except Exception as e:
    logging.error("启动 SUMO 失败: %s", e)
    sys.exit(1)

# 加载 Simpla 配置
try:
    logging.info("Loading Simpla configuration from %s", simpla_cfg)
    simpla.load(simpla_cfg)
except SimplaException as e:
    logging.error("加载 Simpla 配置失败: %s", e)
    traci.close()
    sys.exit(1)

# 初始化碰撞统计
collision_log = []
collision_ids_seen = set()

# 主仿真循环
try:
    while True:
        try:
            traci.simulationStep()
            sim_time_ms = int(traci.simulation.getTime() * 1000)

            # ==== 随机干预车辆以引发碰撞 ====
            if 25200 <= sim_time_ms <= 25500:  # 7小时到7小时15分钟
                vehicle_ids = traci.vehicle.getIDList()
                for vid in vehicle_ids:
                    if random.random() < 0.003:  # 每步干预 0.3% 车辆
                        try:
                            traci.vehicle.setSpeed(vid, 0.1)
                            if traci.vehicle.getLaneIndex(vid) > 0:
                                traci.vehicle.changeLane(vid, traci.vehicle.getLaneIndex(vid) - 1, 0.5)
                        except traci.TraCIException:
                            continue
            # ============================

            # ==== 碰撞检测 ====
            colliding_vehicles = traci.simulation.getCollidingVehiclesIDList()
            for vid in colliding_vehicles:
                if vid not in collision_ids_seen:
                    collision_ids_seen.add(vid)
                    log_entry = f"Collision at {sim_time_ms} ms: vehicle {vid}"
                    collision_log.append(log_entry)
                    logging.info(log_entry)
            # ===================

        except FatalTraCIError as e:
            logging.warning("TraCI 连接被重置（可能是 SUMO 退出）：%s", e)
            break
        except OSError as e:
            logging.warning("底层 Socket 错误：%s", e)
            break
except Exception as e:
    logging.error("仿真过程中发生未预期错误: %s", e)
finally:
    logging.info("关闭 TraCI 连接")
    traci.close()

    # 输出统计结果
    logging.info("仿真结束，共记录碰撞事件：%d 起", len(collision_log))
    if collision_log:
        logging.info("碰撞详细记录如下：")
        for entry in collision_log:
            logging.info(entry)

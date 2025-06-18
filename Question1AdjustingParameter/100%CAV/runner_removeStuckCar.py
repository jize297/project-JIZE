#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runner.py - 控制 SUMO 仿真执行至指定时间，集成 Simpla 控制，包含基本异常处理
"""

import os
import sys
import logging

# 配置日志格式
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# 检查 SUMO_HOME 环境变量
if "SUMO_HOME" not in os.environ:
    sys.exit("❌ 请先设置 SUMO_HOME 环境变量")
tools = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(tools)

import traci
from traci.exceptions import FatalTraCIError
import sumolib
import simpla
from simpla import SimplaException

# 参数配置
USE_GUI = 'nogui' not in sys.argv
SUMO_BINARY = 'sumo-gui' if USE_GUI else 'sumo'
SUMO_CFG = 'M50_simulation.sumocfg'
NET_FILE = 'M50network.net.xml.gz'
SIMPLA_CFG = 'simpla.cfg.xml'
END_TIME = 27000  # 设置仿真结束时间（单位：秒）

# 构建启动命令
sumo_cmd = [
    sumolib.checkBinary(SUMO_BINARY),
    '-c', SUMO_CFG,
    '--net-file', NET_FILE,
    '--step-length', '0.2',
    '--xml-validation.routes', 'never'
]

# 启动 SUMO
logging.info("🚦 启动 SUMO: %s", " ".join(sumo_cmd))
try:
    traci.start(sumo_cmd)
except Exception as e:
    logging.error("❌ 无法启动 SUMO: %s", e)
    sys.exit(1)

# 加载 Simpla
try:
    logging.info("🔧 加载 Simpla 配置: %s", SIMPLA_CFG)
    simpla.load(SIMPLA_CFG)
except SimplaException as e:
    logging.error("❌ 加载 Simpla 失败: %s", e)
    traci.close()
    sys.exit(1)

# 主循环运行到设定时间
try:
    while traci.simulation.getTime() < END_TIME:
        traci.simulationStep()
except FatalTraCIError as e:
    logging.warning("⚠️ TraCI 连接被重置（SUMO 可能已退出）: %s", e)
except Exception as e:
    logging.error("❌ 仿真运行时出错: %s", e)
finally:
    sim_time = traci.simulation.getTime()
    logging.info("🛑 仿真结束，实际时间: %.2f 秒", sim_time)
    traci.close()

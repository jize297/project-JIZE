#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runner.py - 用于整合 SUMO 仿真和 Simpla 控制的入口程序

使用前请确认：
  1. 环境变量 SUMO_HOME 已正确设置。 
  2. SUMO 配置文件 (M50_simulation.sumocfg) 与 Simpla 配置文件 (simpla.cfg.xml) 路径正确。
  3. additional-files (例如 vtypes.add.xml) 能被正确加载。

运行示例：
    python runner.py
    或者禁用 GUI： python runner.py nogui
"""

import os
import sys
import logging

# 设置日志级别为 DEBUG 可查看 SUMO 详细日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# 检查 SUMO_HOME 环境变量
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    if tools not in sys.path:
        sys.path.append(tools)
else:
    sys.exit("请设置环境变量 SUMO_HOME")

import traci
from traci.exceptions import FatalTraCIError
import sumolib
import simpla
from simpla import SimplaException

# 根据命令行参数决定是否使用 GUI
binary = 'sumo-gui'
if 'nogui' in sys.argv:
    binary = 'sumo'

# 文件路径设置
sumo_cfg = 'M50_simulation.sumocfg'
simpla_cfg = 'simpla.cfg.xml'

# 构造 SUMO 命令行参数，并禁用 routes 文件 XSD 校验
sumo_cmd = [
    sumolib.checkBinary(binary),
    '-c', sumo_cfg,
    '--step-length', '0.5',
    '--fcd-output', 'fcd.xml',
    '--fcd-output.max-leader-distance', '100',
    '--xml-validation.routes', 'never',    # 忽略 routes XSD 校验以支持 Simpla 扩展属性
    '--verbose', 'true'                     # 输出更详细的 SUMO 日志
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

# 主仿真循环：处理仿真步骤，并捕获连接重置或 FatalTraCIError
try:
    while True:
        try:
            # 如果需要在固定仿真时间结束，可在此判断时间并 break
            # if traci.simulation.getTime() >= END_TIME: break
            traci.simulationStep()
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
    logging.info("仿真结束")

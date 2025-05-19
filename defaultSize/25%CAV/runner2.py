#!/usr/bin/env python
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

from __future__ import print_function, absolute_import
import os
import sys
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# 检查 SUMO_HOME 环境变量
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    if tools not in sys.path:
        sys.path.append(tools)
else:
    sys.exit("请设置环境变量 SUMO_HOME")

import traci
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

# 构造 SUMO 命令行参数
sumo_cmd = [sumolib.checkBinary(binary),
            '-c', sumo_cfg,
            '--step-length', '0.5',
            '--fcd-output', 'fcd.xml',
            '--fcd-output.max-leader-distance', '100']

logging.info("Starting SUMO with command: %s", " ".join(sumo_cmd))
try:
    traci.start(sumo_cmd)
except Exception as e:
    logging.error("启动 SUMO 失败: %s", e)
    sys.exit(1)

try:
    logging.info("Loading Simpla configuration from %s", simpla_cfg)
    simpla.load(simpla_cfg)
except SimplaException as e:
    logging.error("加载 Simpla 配置失败: %s", e)
    traci.close()
    sys.exit(1)

try:
    # 主仿真循环：当网络中还有车辆时，逐步执行仿真步
    while traci.simulation.getMinExpectedNumber() > 0:
        try:
            traci.simulationStep()
        except Exception as step_err:
            logging.error("仿真步骤异常: %s", step_err)
            break
except Exception as e:
    logging.error("仿真过程中发生未预期错误: %s", e)
finally:
    logging.info("关闭 TraCI 连接")
    traci.close()
    logging.info("仿真结束")

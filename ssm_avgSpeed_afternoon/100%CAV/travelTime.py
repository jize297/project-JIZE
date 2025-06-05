#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计 tripinfo.xml 中出发时间在给定窗口内 (默认 25200–27000 s) 的:
  1) 车辆数量
  2) 平均行程时间
  3) 平均行驶速度 (m/s 与 km/h)

用法:
    python stats_trip_window.py               # 默认 07:00–07:30
    python stats_trip_window.py 25000 30000   # 自定义时间窗
"""

import sys
import xml.etree.ElementTree as ET

XML_FILE      = "tripinfo.xml"   # 相对路径或改成绝对路径
DEFAULT_START = 46800.0          # 07:00
DEFAULT_END   = 50400.0          # 07:30


def main():
    # ───── 解析时间窗参数 ─────
    try:
        start = float(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_START
        end   = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_END
    except ValueError:
        sys.exit("⛔  起止时间必须是数字 (秒)")

    if start > end:
        start, end = end, start   # 允许用户反着写

    # ───── 初始化累加器 ─────
    total_duration = 0.0   # Σ 行驶时间
    total_distance = 0.0   # Σ 行驶距离
    count          = 0

    # ───── 流式遍历 tripinfo.xml ─────
    for _event, elem in ET.iterparse(XML_FILE, events=("end",)):
        if elem.tag == "tripinfo":
            depart  = float(elem.attrib["depart"])
            arrival = float(elem.attrib.get("arrival", "-1"))

            if start <= depart <= end and arrival >= 0:     # 过滤条件
                total_duration += float(elem.attrib["duration"])
                total_distance += float(elem.attrib["routeLength"])
                count          += 1
            elem.clear()   # 及时释放内存

    # ───── 结果输出 ─────
    if count and total_duration:
        mean_duration   = total_duration / count
        mean_speed_mps  = total_distance  / total_duration
        mean_speed_kph  = mean_speed_mps * 3.6

        print(f"📊 depart ∈ [{start}, {end}] 秒")
        print(f"🚗 车辆数量           : {count}")
        print(f"⏱️ 平均行程时间       : {mean_duration:.2f} s")
        print(f"🏎️ 平均速度           : {mean_speed_mps:.2f} m/s  ≈ {mean_speed_kph:.2f} km/h")
    else:
        print("⚠️  指定时间窗内没有已到达的车辆")


if __name__ == "__main__":
    main()

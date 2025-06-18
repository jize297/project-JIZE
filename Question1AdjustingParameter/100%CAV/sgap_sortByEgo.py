#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from collections import defaultdict

# ———— 这里直接固定输入/输出文件名 ————
SSM_FILE       = 'ssm_CAV2.xml'   # SSMLog 文件名
TRIPINFO_FILE  = 'tripinfo.xml'             # tripinfo.xml 文件名
OUTPUT_FILE    = 'minSGAP_summaryCAV2.txt'      # 输出文件名
# 时间窗口可按需调整
TIME_WINDOW    = (25200.0, 28800.0)
# ————————————————————————————————————

def load_vehicle_types(tripinfo_file):
    """
    解析 tripinfo.xml，构造 vehicle_id -> vType 的字典
    """
    tree = ET.parse(tripinfo_file)
    root = tree.getroot()
    id_to_type = {}
    for trip in root.findall('.//tripinfo'):
        vid   = trip.get('id')
        vtype = trip.get('vType')
        if vid and vtype:
            id_to_type[vid] = vtype
    return id_to_type

def analyze_min_sgap(ssm_file, id_to_type, t_start, t_end):
    """
    解析 SSMLog（含 globalMeasures），筛选 minSGAP 时间在 [t_start, t_end] 内的记录，
    并按 leader 的 vType 分类返回字典：{leader_vtype: [record, ...]}
    """
    tree = ET.parse(ssm_file)
    root = tree.getroot()

    by_type = defaultdict(list)

    for gm in root.findall('.//globalMeasures'):
        # 找到 <minSGAP .../> 子元素
        min_elem = gm.find('minSGAP')
        if min_elem is None:
            continue

        time_str = min_elem.get('time')
        try:
            t = float(time_str)
        except (TypeError, ValueError):
            continue

        # 仅保留在时间窗口内的记录
        if not (t_start <= t <= t_end):
            continue

        ego       = gm.get('ego')
        leader_id = min_elem.get('leader')
        sgap_val  = min_elem.get('value')
        position  = min_elem.get('position')

        # 根据 leader_id 查找它在 tripinfo.xml 中的 vType
        ego_vtype = id_to_type.get(ego, 'UNKNOWN')

        by_type[ego_vtype].append({
            'ego':        ego,
            'leader':     leader_id,
            'time':       time_str,
            'position':   position,
            'minSGAP':    sgap_val
        })

    return by_type

def write_summary(by_type, output_file):
    """
    把按 leader_vType 分类的 minSGAP 记录写到 text 文件里
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for vtype, records in by_type.items():
            f.write(f"{vtype}\n")
            f.write(f"{'=' * len(vtype)}\n")
            f.write(f"Total Records: {len(records)}\n")
            for r in records:
                f.write(
                    f"  Ego: {r['ego']}, Leader: {r['leader']}, "
                    f"Time: {r['time']}, Position: {r['position']}, minSGAP: {r['minSGAP']}\n"
                )
            f.write("\n")
    print(f"✅ 已生成：{output_file}")

def main():
    print("🔍 载入车辆类型……")
    id2type = load_vehicle_types(TRIPINFO_FILE)

    print(f"📑 解析 minSGAP 记录（时间窗口 {TIME_WINDOW[0]}–{TIME_WINDOW[1]} 秒）……")
    by_type = analyze_min_sgap(SSM_FILE, id2type, *TIME_WINDOW)

    print("✍️ 写入汇总……")
    write_summary(by_type, OUTPUT_FILE)

if __name__ == '__main__':
    main()

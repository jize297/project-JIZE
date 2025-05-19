import xml.etree.ElementTree as ET
import sumolib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

def parse_edge_speeds(xml_file, interval_index=-1):
    """
    解析 edge_output.xml，返回指定 interval_index 中
    每条Edge的 speed (m/s)。若 interval_index=-1，表示取最后一个interval。
    
    返回: { edge_id: speed_value_in_m_s, ... }
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    intervals = root.findall('interval')
    if not intervals:
        raise ValueError("No <interval> found in the XML.")
    
    # interval_index 可能超出范围，这里做个保护
    if interval_index < 0:
        interval_index = len(intervals) - 1  # 最后一个
    if interval_index >= len(intervals):
        interval_index = len(intervals) - 1
    
    chosen_interval = intervals[interval_index]
    
    edge_speed_map = {}
    for edge_elem in chosen_interval.findall('edge'):
        edge_id = edge_elem.get('id')
        speed_str = edge_elem.get('speed')
        if speed_str:
            speed_val = float(speed_str)  # m/s
            edge_speed_map[edge_id] = speed_val
    
    return edge_speed_map, chosen_interval


def speed_to_travelrate(speed_m_s):
    """
    将速度(m/s)转换为Travel Rate (min/km)。
    公式: TravelRate = (1000 / speed) / 60 = 1000/(60*speed)
    如果speed很小或为0，这里返回一个较大值(例如 3.0 代表3min/km)，
    你可自行处理。
    """
    if speed_m_s <= 0.0001:
        return 3.0  # 或者返回 float('inf')，或其他上限
    return 1000.0 / (60.0 * speed_m_s)


def plot_travel_rate_on_net(net_file, edge_travelrate_map, out_png="output_map.png",
                            vmin=0.5, vmax=2.0, title="Travel Rate (min/km)"):
    """
    在 SUMO 路网上，根据edge_travelrate_map做颜色渐变可视化
    
    net_file:   SUMO网络文件 .net.xml
    edge_travelrate_map: {edge_id: travelRate (min/km)}
    vmin, vmax: 颜色映射区间
    out_png:    保存图片名
    """
    # 1. 读取路网
    net = sumolib.net.readNet(net_file)
    
    # 2. 准备画布
    fig, ax = plt.subplots(figsize=(6, 8))
    ax.set_aspect('equal', adjustable='datalim')
    ax.axis('off')  # 不要坐标轴

    # 3. colormap
    cmap = cm.get_cmap('RdBu_r')  # 红到蓝 (反转)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    # 4. 遍历所有edge并画线
    for edge in net.getEdges():
        e_id = edge.getID()
        shape = edge.getShape()  # list of (x, y)
        
        # 找该edge的travelRate
        val = edge_travelrate_map.get(e_id, None)
        if val is None:
            # 该edge没有数据，就跳过或给默认值
            continue
        
        color = cmap(norm(val))
        
        x_coords = [p[0] for p in shape]
        y_coords = [p[1] for p in shape]
        ax.plot(x_coords, y_coords, color=color, linewidth=3)

    # 5. colorbar
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])  # 没有实际数据阵列也没事
    cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Travel Rate (min/km)")

    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.show()


if __name__ == "__main__":
    # 1. 解析 edge_output.xml
    edge_output_xml = "edge_output.xml"  # 你实际的路径
    # 选择一个 interval，-1 表示最后一个时间段
    edge_speed_map, the_interval = parse_edge_speeds(edge_output_xml, interval_index=-1)
    
    # 2. 把速度转成 TravelRate
    edge_tr_map = {}
    for e_id, speed_val in edge_speed_map.items():
        tr = speed_to_travelrate(speed_val)
        edge_tr_map[e_id] = tr
    
    # 3. 画图
    net_file = "M50network.net.xml"  # 你的网络文件
    begin_str = the_interval.get('begin')
    end_str   = the_interval.get('end')
    time_title = f"{begin_str} - {end_str}s Travel Rate"
    
    # 你可根据实际 min/max 值调整 vmin, vmax
    plot_travel_rate_on_net(
        net_file, 
        edge_tr_map,
        out_png="m50_travelrate.png",
        vmin=0.5,
        vmax=3.0,  
        title=time_title
    )

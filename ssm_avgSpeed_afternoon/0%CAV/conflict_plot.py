import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

# 用户请根据实际文件名修改路径
net_file = 'M50network.net.xml'       # 你的 net.xml 路径
ssm_file = 'ssm_CAV2.xml'   # 你的 SSM 输出 XML 路径

# 1. 解析 road network，提取所有 lane 的 shape 坐标
tree_net = ET.parse(net_file)
root_net = tree_net.getroot()

lane_shapes = []
for lane in root_net.findall('.//lane'):
    shape = lane.get('shape')
    if shape:
        pts = [tuple(map(float, coord.split(','))) for coord in shape.split()]
        lane_shapes.append(pts)

# 2. 解析 SSM 文件，筛选指定时间窗口的冲突点
tree_ssm = ET.parse(ssm_file)
root_ssm = tree_ssm.getroot()

t_start, t_end = 25200, 27000
filtered_points = []
count_conflicts = 0

for c in root_ssm.findall('.//conflict'):
    begin = float(c.get('begin'))
    if t_start <= begin <= t_end:
        # 优先取 minTTC 的位置
        elem = c.find('minTTC')
        pos = elem.get('position')
        if pos and pos != 'NA':
            x, y = map(float, pos.split(','))
            filtered_points.append((x, y))
            count_conflicts += 1

# 3. 绘图：网络 + 冲突点
plt.figure(figsize=(12, 8))
# 绘制道路网络
for pts in lane_shapes:
    xs, ys = zip(*pts)
    plt.plot(xs, ys, color='gray', linewidth=0.5)

# 绘制冲突点
if filtered_points:
    xs, ys = zip(*filtered_points)
    plt.scatter(xs, ys, c='red', marker='x', s=50, label=f'Conflicts ({count_conflicts})')

plt.axis('equal')
plt.title(f'CAV2 as ego car(10%cav): Conflict Points between {t_start}s and {t_end}s (Total={count_conflicts})')
plt.xlabel('X coordinate')
plt.ylabel('Y coordinate')
plt.legend()
plt.tight_layout()
plt.show()

# 输出统计结果
print(f"在 {t_start} 到 {t_end} 秒区间内，共检测到 {count_conflicts} 次冲突并绘制在图上。")

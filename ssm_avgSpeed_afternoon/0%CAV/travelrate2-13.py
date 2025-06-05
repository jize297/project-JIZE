import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import sumolib           # Ensure you have sumolib installed
from matplotlib_scalebar.scalebar import ScaleBar  # pip install matplotlib-scalebar
import csv

# 1. Load the network
net = sumolib.net.readNet('M50network.net.xml')

# 2. Parse meandata_A.xml and compute average TR per edge
meandata = 'edge_output.xml'
tree = ET.parse(meandata)
root = tree.getroot()

tr_sum, count = {}, {}
for interval in root.findall('interval'):
    for edge in interval.findall('edge'):
        eid = edge.attrib['id']
        speed = float(edge.attrib.get('speed', 0.0))  # km/h
        if speed > 0:
            tr = 60.0 / speed
            tr_sum[eid] = tr_sum.get(eid, 0.0) + tr
            count[eid] = count.get(eid, 0) + 1

avg_tr = {eid: tr_sum[eid] / count[eid] for eid in tr_sum}

# 3. Build segments and output TR info
lines, colors = [], []
segments_info = []  # To store segment info

for edge in net.getEdges():
    shape = edge.getShape()
    eid = edge.getID()
    tr_val = avg_tr.get(eid, np.nan)
    for i in range(len(shape) - 1):
        seg = [shape[i], shape[i + 1]]
        lines.append(seg)
        colors.append(tr_val)
        segment_id = f"{eid}_{i}"
        segments_info.append({
            'segment_id': segment_id,
            'edge_id': eid,
            'travel_rate': tr_val
        })

# 4. Write segment info to CSV
csv_file = 'segment2_travel_rates.csv'
with open(csv_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['segment_id', 'edge_id', 'travel_rate'])
    writer.writeheader()
    for row in segments_info:
        writer.writerow(row)

print(f"Segment travel rates written to: {csv_file}")

# 5. Plot
fig, ax = plt.subplots(figsize=(6, 8))
lc = LineCollection(
    lines,
    array=np.array(colors),
    cmap='coolwarm',
    norm=plt.Normalize(vmin=2, vmax=13.0),
    linewidths=2)
ax.add_collection(lc)
ax.autoscale()
ax.set_aspect('equal')
ax.axis('off')

# Add scale bar
scalebar = ScaleBar(dx=1, units='m', length_fraction=0.2,
                    location='lower left', scale_loc='bottom')
ax.add_artist(scalebar)
ax.text(0.22, 0.08, '1000 m', transform=ax.transAxes, va='bottom', fontsize=12)

# Colorbar
cbar = fig.colorbar(lc, ax=ax, orientation='vertical',
                    fraction=0.03, pad=0.02)
cbar.set_label('Travel Rate (min/km)', fontsize=12)

plt.title('Scenario A: Detailed Segment Travel Rate', fontsize=14, pad=12)
plt.tight_layout()
plt.show()

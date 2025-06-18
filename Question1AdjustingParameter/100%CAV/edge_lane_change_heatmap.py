#!/usr/bin/env python3
"""
edge_lane_change_heatmap.py

Plot heatmap of lane-change frequency on network with fixed parameters.
"""
import os
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib_scalebar.scalebar import ScaleBar
import csv
import sumolib

# Fixed parameters
NET_FILE = 'M50network.net.xml'
EDGE_OUTPUT_FILE = 'edge_output.xml'
OUTPUT_CSV = 'segment_lane_changes.csv'
CMAP = 'plasma'
VMIN = 0.0
VMAX = 10.0


def main():
    # 1. Load the network
    net = sumolib.net.readNet(NET_FILE)

    # 2. Parse edge_output.xml and compute average lane-change count per edge
    lane_change_sum = {}
    count = {}

    tree = ET.parse(EDGE_OUTPUT_FILE)
    root = tree.getroot()

    for interval in root.findall('interval'):
        for edge in interval.findall('edge'):
            eid = edge.attrib['id']
            lc_from = float(edge.attrib.get('laneChangedFrom', 0.0))
            if lc_from > 0:
                lane_change_sum[eid] = lane_change_sum.get(eid, 0.0) + lc_from
                count[eid] = count.get(eid, 0) + 1

    avg_lane_changes = {eid: lane_change_sum[eid] / count[eid] for eid in lane_change_sum}

    # 3. Build segments and collect lane-change info
    lines = []
    colors = []
    segment_info = []

    for edge in net.getEdges():
        shape = edge.getShape()
        eid = edge.getID()
        lc_val = avg_lane_changes.get(eid, np.nan)
        for i in range(len(shape) - 1):
            seg = [shape[i], shape[i + 1]]
            lines.append(seg)
            colors.append(lc_val)
            segment_id = f"{eid}_{i}"
            segment_info.append({
                'segment_id': segment_id,
                'edge_id': eid,
                'avg_lane_changes': lc_val
            })

    # 4. Write segment info to CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV) or '.', exist_ok=True)
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['segment_id', 'edge_id', 'avg_lane_changes'])
        writer.writeheader()
        for row in segment_info:
            writer.writerow(row)
    print(f"Segment lane-change data written to: {OUTPUT_CSV}")

    # 5. Plot heatmap on map
    fig, ax = plt.subplots(figsize=(8, 6))
    lc = LineCollection(
        lines,
        array=np.array(colors),
        cmap=CMAP,
        norm=plt.Normalize(vmin=VMIN, vmax=VMAX),
        linewidths=2
    )
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
    cbar.set_label('Average Lane Changes per Interval', fontsize=12)

    plt.title('Heatmap: Lane-Change Frequency per Lane Segment', fontsize=14, pad=12)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
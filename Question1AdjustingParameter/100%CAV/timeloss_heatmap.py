#!/usr/bin/env python3
"""
edge_timeloss_heatmap.py

Plot heatmap of time loss on network with fixed parameters.
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
OUTPUT_CSV = 'segment_time_loss.csv'

# Time-loss heatmap params
TL_CMAP = 'viridis'
TL_VMIN = 0.0
TL_VMAX = 100.0


def main():
    # 1. Load the network
    net = sumolib.net.readNet(NET_FILE)

    # 2. Parse edge_output.xml and compute average time-loss per edge
    tl_sum = {}
    count = {}

    tree = ET.parse(EDGE_OUTPUT_FILE)
    root = tree.getroot()

    for interval in root.findall('interval'):
        for edge in interval.findall('edge'):
            eid = edge.attrib['id']
            tl = float(edge.attrib.get('timeLoss', 0.0))
            tl_sum[eid] = tl_sum.get(eid, 0.0) + tl
            count[eid] = count.get(eid, 0) + 1

    avg_tl = {eid: tl_sum[eid] / count[eid] for eid in tl_sum}

    # 3. Build segments and collect time-loss info
    lines = []
    colors = []
    segment_info = []

    for edge in net.getEdges():
        shape = edge.getShape()
        eid = edge.getID()
        tl_val = avg_tl.get(eid, np.nan)
        for i in range(len(shape) - 1):
            seg = [shape[i], shape[i + 1]]
            lines.append(seg)
            colors.append(tl_val)
            segment_info.append({
                'segment_id': f"{eid}_{i}",
                'edge_id': eid,
                'avg_time_loss': tl_val
            })

    # 4. Write segment time-loss to CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV) or '.', exist_ok=True)
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['segment_id', 'edge_id', 'avg_time_loss'])
        writer.writeheader()
        for row in segment_info:
            writer.writerow(row)
    print(f"Segment time-loss data written to: {OUTPUT_CSV}")

    # 5. Plot time-loss heatmap
    fig, ax = plt.subplots(figsize=(8, 6))
    tl_collection = LineCollection(
        lines,
        array=np.array(colors),
        cmap=TL_CMAP,
        norm=plt.Normalize(vmin=TL_VMIN, vmax=TL_VMAX),
        linewidths=2
    )
    ax.add_collection(tl_collection)
    ax.autoscale()
    ax.set_aspect('equal')
    ax.axis('off')

    # Add scale bar
    scalebar = ScaleBar(dx=1, units='m', length_fraction=0.2,
                        location='lower left', scale_loc='bottom')
    ax.add_artist(scalebar)
    ax.text(0.22, 0.08, '1000 m', transform=ax.transAxes, va='bottom', fontsize=12)

    # Colorbar
    cbar = fig.colorbar(tl_collection, ax=ax, orientation='vertical', fraction=0.03, pad=0.02)
    cbar.set_label('Avg Time Loss per Interval', fontsize=12)

    plt.title('Heatmap: Time Loss per Segment', fontsize=14, pad=12)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

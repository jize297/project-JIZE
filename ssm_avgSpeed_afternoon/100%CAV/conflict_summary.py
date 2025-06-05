import xml.etree.ElementTree as ET
from collections import defaultdict
import argparse

def load_vehicle_types(tripinfo_file):
    """
    Parse tripinfo.xml and build a mapping from vehicle ID to vehicle type (vType attribute).
    """
    tree = ET.parse(tripinfo_file)
    root = tree.getroot()
    id_to_type = {}
    # Find all tripinfo entries
    for trip in root.findall('.//tripinfo'):
        vid = trip.get('id')
        vtype = trip.get('vType')
        if vid and vtype:
            id_to_type[vid] = vtype
    return id_to_type


def analyze_conflicts(ssm_file, id_to_type, start_time=25200, end_time=28800):
    """
    Parse ssm_CAV2.xml conflicts, filter by begin time between start_time and end_time (in seconds),
    and categorize conflicts by foe vehicle type.
    Returns a dict: foe_type -> list of conflict details
    """
    tree = ET.parse(ssm_file)
    root = tree.getroot()
    by_type = defaultdict(list)

    for conflict in root.findall('.//conflict'):
        begin = conflict.get('begin')
        try:
            t_begin = float(begin)
        except (TypeError, ValueError):
            # Skip entries without a valid begin time
            continue
        # Filter by the desired time window
        if not (start_time <= t_begin <= end_time):
            continue

        ego = conflict.get('ego')
        full_foe = conflict.get('foe')          # e.g. "NRA_000000001070_Eastbound-4.1354"
        foe_id = full_foe if full_foe else None  # keep entire ID including suffix
        foe_type = id_to_type.get(foe_id, 'UNKNOWN')

        end_t = conflict.get('end')
        min_ttc_elem = conflict.find('minTTC')
        ttc_val = min_ttc_elem.get('value') if min_ttc_elem is not None else None

        by_type[foe_type].append({
            'ego': ego,
            'foe': foe_id,
            'foe_type': foe_type,
            'begin': begin,
            'end': end_t,
            'minTTC': ttc_val
        })
    return by_type


def write_summary(by_type, output_file):
    """
    Write a summary of conflicts per foe type into a text file, using foe type as section title.
    """
    with open(output_file, 'w') as f:
        for vtype, conflicts in by_type.items():
            f.write(f"{vtype}\n")
            f.write(f"{'=' * len(vtype)}\n")
            f.write(f"Total Conflicts: {len(conflicts)}\n")
            for c in conflicts:
                f.write(
                    f"  Ego: {c['ego']}, Foe: {c['foe']}, "
                    f"Foe Type: {c['foe_type']}, "
                    f"Time: {c['begin']}-{c['end']}, minTTC: {c['minTTC']}\n"
                )
            f.write("\n")
    print(f"Summary written to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Classify and filter CAV2 conflicts by foe type and time window.')
    parser.add_argument('ssm_file', help='Path to ssm_CAV2.xml')
    parser.add_argument('tripinfo_file', help='Path to tripinfo.xml')
    parser.add_argument('-o', '--output', default='conflict_summary.txt',
                        help='Output file path (default: conflict_summary.txt)')
    parser.add_argument('--start', type=float, default=25200,
                        help='Start time in seconds for filtering conflicts (default: 25200)')
    parser.add_argument('--end', type=float, default=28800,
                        help='End time in seconds for filtering conflicts (default: 28800)')
    args = parser.parse_args()

    id_to_type = load_vehicle_types(args.tripinfo_file)
    by_type = analyze_conflicts(args.ssm_file, id_to_type, args.start, args.end)
    write_summary(by_type, args.output)

if __name__ == '__main__':
    main()

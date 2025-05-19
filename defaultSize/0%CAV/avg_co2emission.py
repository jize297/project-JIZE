import xml.etree.ElementTree as ET
import csv

def parse_emissions(file_path, start_time=25200.0, end_time=26100.0):
    """
    解析 emission.xml，统计每个 timestep 内的 CO2 排放总量、燃料消耗总量和车辆数。

    :param file_path: emission.xml 文件路径
    :param start_time: 开始时间（包含）
    :param end_time: 结束时间（包含）
    :return: 按时间排序的列表，每项为 (time, total_co2, total_fuel, vehicle_count)
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    results = []
    for ts in root.findall('timestep'):
        time = float(ts.get('time'))
        if start_time <= time <= end_time:
            vehicles = ts.findall('vehicle')
            total_co2 = sum(float(v.get('CO2', 0.0)) for v in vehicles)
            total_fuel = sum(float(v.get('fuel', 0.0)) for v in vehicles)
            count = len(vehicles)
            results.append((time, total_co2, total_fuel, count))

    results.sort(key=lambda x: x[0])
    return results

if __name__ == '__main__':
    input_file = 'emission.xml'  # 替换为你的文件路径
    output_file = 'emission_summary.csv'
    data = parse_emissions(input_file, 25200.0, 26100.0)

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['time', 'total_co2', 'total_fuel', 'vehicle_count'])
        for time, co2, fuel, count in data:
            writer.writerow([f"{time:.2f}", f"{co2:.2f}", f"{fuel:.2f}", count])

    print(f"结果已保存到 {output_file}")

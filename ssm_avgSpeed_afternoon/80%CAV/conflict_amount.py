import xml.etree.ElementTree as ET
import pandas as pd

# 1. 指定你的 SSM 输出文件路径
xml_file = 'ssm_HDC.xml'  # 或者换成你的文件名

# 2. 解析 XML
tree = ET.parse(xml_file)
root = tree.getroot()

# 3. 提取所有 <conflict> 信息
records = []
for c in root.findall('.//conflict'):
    records.append({
        'ego':        c.get('ego'),
        'foe':        c.get('foe'),
        'begin_time': float(c.get('begin')),
        'end_time':   float(c.get('end')),
        'minTTC':     float(c.find('minTTC').get('value'))     if c.find('minTTC').get('value')     != 'NA' else None,
        'maxDRAC':    float(c.find('maxDRAC').get('value'))    if c.find('maxDRAC').get('value')    != 'NA' else None,
        'maxMDRAC':   float(c.find('maxMDRAC').get('value'))   if c.find('maxMDRAC').get('value')   != 'NA' else None
    })

# 4. 构建 DataFrame
df = pd.DataFrame(records)

# 5. 基本统计
total = len(df)
ego_counts = df['ego'].value_counts()
foe_counts = df['foe'].value_counts()

# 6. 输出结果
print(f"总冲突数: {total}\n")

print("按 Ego 车辆统计冲突次数：")
print(ego_counts.to_string(), "\n")

print("按 Foe 车辆统计冲突次数：")
print(foe_counts.to_string(), "\n")

print("前几条冲突详情预览：")
print(df.head().to_string(index=False))

# 7. 保存到 CSV，方便后续分析
df.to_csv('conflicts.csv', index=False)
print("\n详细冲突列表已保存到: conflicts.csv")

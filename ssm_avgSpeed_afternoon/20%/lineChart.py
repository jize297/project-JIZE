import matplotlib.pyplot as plt
import pandas as pd

# 构造数据
data = {
    'CAV rate': ['25% CAV', '50% CAV', '100% CAV'],
    'average travel time (s)': [235.44, 231.35 , 228.65]
}
df = pd.DataFrame(data)

# 绘制折线图
plt.figure()
plt.plot(df['CAV rate'], df['average travel time (s)'], marker='o', label='average travel time (s)')
plt.xlabel('CAV rate')
plt.ylabel('average travel time (s)')
plt.title('different average travel time under different CAV rate')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

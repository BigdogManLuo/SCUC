import pulp

# 创建一个线性规划问题
prob = pulp.LpProblem("Unit_Commitment", pulp.LpMinimize)

# 时间段（小时）
time_periods = [0, 1] 

# 发电机信息（假设有3个发电机）
generators = ['Gen1', 'Gen2', 'Gen3']
min_power = {'Gen1': 50, 'Gen2': 30, 'Gen3': 40}  # 最小出力（MW）
max_power = {'Gen1': 200, 'Gen2': 150, 'Gen3': 120}  # 最大出力（MW）
startup_cost = {'Gen1': 100, 'Gen2': 80, 'Gen3': 90}  # 启动成本
shutdown_cost = {'Gen1': 70, 'Gen2': 60, 'Gen3': 50}  # 停机成本
operating_cost = {'Gen1': 10, 'Gen2': 12, 'Gen3': 15}  # 每单位电力的运营成本（$/MW）

# 电力需求（假设每个时间段的需求）
demand = {0: 150, 1: 180}

# 创建决策变量
# u_t_g = 1 如果在时间段t启动发电机g，否则为0
u = pulp.LpVariable.dicts("u", ((t, g) for t in time_periods for g in generators), 0, 1, pulp.LpBinary)

# p_t_g = 发电机g在时间段t的输出功率（MW）
p = pulp.LpVariable.dicts("p", ((t, g) for t in time_periods for g in generators), 0)

# 目标函数：最小化总成本（启动成本 + 关机成本 + 操作成本）
prob += pulp.lpSum(startup_cost[g] * u[t, g] + shutdown_cost[g] * (1 - u[t, g]) + operating_cost[g] * p[t, g] 
                   for t in time_periods for g in generators), "Total Cost"

# 约束条件：
# 1. 每个时间段的发电量需要满足需求
for t in time_periods:
    prob += pulp.lpSum(p[t, g] for g in generators) == demand[t], f"Demand_{t}"

# 2. 每个发电机的功率输出必须在最小和最大范围之间
for t in time_periods:
    for g in generators:
        if g!='Gen1':
            prob += p[t, g] >= min_power[g] * u[t, g], f"Min_Power_{t}_{g}"
            prob += p[t, g] <= max_power[g] * u[t, g], f"Max_Power_{t}_{g}"

# 3. 发电机的启动约束：如果一个发电机在时间段t运行，且在t-1时间段内没有运行，它需要启动
for t in range(1, len(time_periods)):
    for g in generators:
        prob += u[t, g] >= u[t-1, g], f"Startup_{t}_{g}"

# 4. 每个时间段只能选择一个发电机的开关状态
for t in time_periods:
    for g in generators:
        prob += u[t, g] <= 1, f"Commit_{t}_{g}"

# 求解问题
prob.solve()

# 打印最优解
print(f"Status: {pulp.LpStatus[prob.status]}")
for t in time_periods:
    for g in generators:
        print(f"Time {t} - Generator {g}: u = {pulp.value(u[t, g])}, p = {pulp.value(p[t, g])} MW")

# 保存问题为.mps文件
prob.writeMPS("data/simple_uc.mps")

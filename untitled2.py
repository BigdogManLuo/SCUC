import pulp
from pulp import LpMaximize, LpProblem, LpVariable, PULP_CBC_CMD,LpMinimize

# 创建一个最大化问题
model = LpProblem("Z", LpMaximize)

# 定义决策变量
x = LpVariable('x', lowBound=0, upBound=1,cat='Integer')  # x 是整数变量，且大于等于 1
y = LpVariable('y')  # y 是连续变量，且大于等于 2

# 目标函数
model += 3 * x + 5 * y, "Z"

# 添加约束条件
model += x + y <= 7
model += 2*x + 4*y <= 10
model += x >= 1
model += y <=4
model  += y >=1
model += 3*x-2*y>=0

#写入到.mps文件
print(model.sense)
model.writeMPS("data/test.mps")


# 求解模型
model.solve(PULP_CBC_CMD(msg=True))

# 输出结果
if model.status == 1:  # 1 表示问题可解
    print(f"Optimal solution found:")
    print(f"x = {x.varValue}")
    print(f"y = {y.varValue}")
    print(f"Objective value (Z) = {model.objective.value()}")
else:
    print("No feasible solution found.")


#%%
import cvxpy as cp

# 定义决策变量
x = cp.Variable(boolean=True)  # x 是整数变量
y = cp.Variable()  # y 是连续变量

# 定义目标函数
objective = cp.Maximize(3 * x + 2 * y)

# 定义约束
constraints = [
    x + y <= 5,  # x + y <= 5
    x >= 1,       # x >= 1
    y >= 2,       # y >= 2
    x <= 1        # x 的取值范围是 0 到 1
]

# 定义优化问题
problem = cp.Problem(objective, constraints)

# 求解问题
problem.solve()

# 输出结果
if problem.status == cp.OPTIMAL:
    print(f"Optimal solution found:")
    print(f"x = {x.value}")
    print(f"y = {y.value}")
    print(f"Objective value (Z) = {problem.value}")
else:
    print("No feasible solution found.")

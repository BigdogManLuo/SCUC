from gurobipy import Model

# 读取 MPS 文件
model = Model()
model.read("path_to_your_model.mps")

# 求解模型
model.optimize()

# 检查约束的对偶值（仅适用于 LP）
if model.status == 2:  # 2 表示 Optimal
    print("Optimal solution found.")
    for constr in model.getConstrs():
        print(f"Constraint {constr.constrName}: dual value = {constr.Pi}")
else:
    print(f"Solver status: {model.status}")
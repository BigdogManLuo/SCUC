from pyscipopt import Model
import time
def solve_mps_file(mps_file_path):
    
    # 创建一个 SCIP 模型
    model = Model("MPS Model")

    # 读取 .mps 文件
    model.readProblem(mps_file_path)
    
    model.setRealParam("limits/time", 7200)
    model.setRealParam("limits/gap", 1e-3)
    model.setIntParam("parallel/maxnthreads", 32)  

    
    # 求解模型
    start=time.time()
    model.optimize()
    end=time.time()
    print(f"Time used: {end-start} seconds")

    # 检查是否找到最优解
    if model.getStatus() == "optimal":
        print("Optimal solution found!")
    else:
        print(f"Model status: {model.getStatus()}")
    
    
    
    # 返回模型对象
    return model



mps_file_path = "data/3_model.mps" 
model = solve_mps_file(mps_file_path)


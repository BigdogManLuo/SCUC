import pulp
import time 


def read_mps(mps_file,sense):
    
    print(f"Reading MPS file: {mps_file}")
    try:
        variables, problem = pulp.LpProblem.fromMPS(mps_file)
    except Exception as e:
        print(f"Error reading MPS file: {e}")
        return None
    
    #pulp读mps文件的bug，需要手动设置sense
    problem.sense=sense
    
    return problem


def solve_mps_with_gurobi(problem):
    
    solver = pulp.GUROBI_CMD(
        msg=True,
        options=[("MIPGap", "1e-4")]
    )
    
    #solver=pulp.PULP_CBC_CMD(msg=False)
    
    print("Solving the problem using Gurobi...")
    print(f"Problem name: {problem.name}")
    print(f"Number of variables: {len(problem.variables())}")
    print(f"Number of constraints: {len(problem.constraints)}")
    
    #计时
    start_time = time.time()
    result = problem.solve(solver)
    elapsed_time = time.time() - start_time

    if pulp.LpStatus[result] == "Optimal":
        print("Optimal solution found, elapsed time: {:.2f} seconds.".format(elapsed_time))
        print(f"Objective value: {pulp.value(problem.objective)}")
    else:
        print(f"Solver status: {pulp.LpStatus[result]}.")
    

    print("------------------------------------")
    
    return problem


def find_active_set_by_manual_slack(problem):
    
    a=0
    active_set = []
    for idx, (name, constraint) in enumerate(problem.constraints.items()):
        
        lhs_value=0
        slack=0
        
        #等式约束是活动的
        if constraint.sense == pulp.LpConstraintEQ:
            active_set.append(name)
            continue
        
        else:
            
            # 计算松弛度
            for var, coef in constraint.items():
                
                if var.varValue is not None:
                    lhs_value += var.varValue * coef
                else:
                    #print(f"Skipping variable {var.name} with undefined value in constraint {name}.")
                    pass
                
            slack = constraint.constant + lhs_value
            
            if abs(slack) < 1e-2: 
                active_set.append(name) 
            else:
                a+=1
                pass
            
    return active_set

def create_reduced_problem(problem, active_set):

    reduced_problem = pulp.LpProblem(f"{problem.name}_reduced", problem.sense)
    
    # 复制目标函数
    reduced_problem+=problem.objective

    # 仅保留活动约束
    for name in active_set:
        #if name in problem.constraints:
        cons=problem.constraints[name]
        cons.sense=pulp.LpConstraintEQ
        reduced_problem += cons

    return reduced_problem


def check_constraints(reduced_problem,original_problem):

    variables =  {var.name: var for var in problem.variables()}
    violate_cons_name=[]
    #检查对于原问题的每一条约束，reduced_problem的最优解是否满足
    for idx, (name, constraint) in enumerate(original_problem.constraints.items()):

        lhs_value = 0
        slack = 0

        for var, coef in constraint.items():
            if var.varValue is not None:
                lhs_value+= variables[var.name].varValue*coef

        slack = constraint.constant + lhs_value

        if constraint.sense == pulp.LpConstraintLE:
            if slack > 1e-4:
                print(f"<=Constraint {name} is violated: {slack}.")
                violate_cons_name.append(name)
        elif constraint.sense == pulp.LpConstraintGE:
            if slack < -1e-4:
                print(f">=Constraint {name} is violated: {slack}.")
                violate_cons_name.append(name)
        elif constraint.sense == pulp.LpConstraintEQ:
            if abs(slack) > 1e-4:
                print(f"==Constraint {name} is violated: {slack}.")
                violate_cons_name.append(name)
        else:
            print(f"Unknown constraint sense: {constraint.sense}.")

    print("Constraint check completed.")

    return violate_cons_name

def solve_mps_with_SCIP(problem):

    solver = pulp.SCIP_CMD(
        path="D:/SCIPOptSuite 9.2.0/bin/scip.exe",
        msg=True,
        options=["limits/gap = 0.0001"]
    )
    print("Solving the problem using SCIP...")
    print(f"Problem name: {problem.name}")
    print(f"Number of variables: {len(problem.variables())}")
    print(f"Number of constraints: {len(problem.constraints)}")
    # 计时
    start_time = time.time()
    result = problem.solve(solver)
    elapsed_time = time.time() - start_time
    if pulp.LpStatus[result] == "Optimal":
        print("Optimal solution found, elapsed time: {:.2f} seconds.".format(elapsed_time))
        print(f"Objective value: {pulp.value(problem.objective)}")
    else:
        print(f"Solver status: {pulp.LpStatus[result]}.")

    print("------------------------------------")
    return problem

if __name__ == "__main__":
    
    mps_file_path = "data/uccase8.mps"  
    
    problem = read_mps(mps_file_path,sense=pulp.LpMinimize)
    
    #problem=solve_mps_with_gurobi(problem)
    problem=solve_mps_with_SCIP(problem)
    
    '''
    active_set=find_active_set_by_manual_slack(problem)
    
    reduced_problem=create_reduced_problem(problem, active_set)

    reduced_problem=solve_mps_with_gurobi(reduced_problem)
    
    violate_cons_name=check_constraints(reduced_problem,problem)
    '''
    
    '''
    for var in problem.variables():
        print(var.name,var.varValue)
    print("objective value:",problem.objective.value())
    
    print("--------------------")
    
    for var in reduced_problem.variables():
        print(var.name,var.varValue)
    print("objective value:",reduced_problem.objective.value())
    '''
    
'''
#检查"Bga(101,1)"变量是否在变量中
for idx,var in enumerate(reduced_problem.variables()):
    if var.name=="Bga(101,1)":
        print(idx,var)
        break


#problem.constraints.items() 写入记事本

with open("data/constraints.txt","w") as f:

    for idx, (name, constraint) in enumerate(reduced_problem.constraints.items()):
        f.write(f"{name}:\n")
        for var, coef in constraint.items():
            f.write(f"{var.name} {coef}\n")
        f.write("\n")
'''


#基于直觉，手动补偿
'''
#elif "Max_Power" in constraint.name or "Min_Power" in constraint.name:
elif "pmin" in constraint.name or "pmax" in constraint.name or "reserva_giro" in constraint.name or "costo_partida" in constraint.name :
    #active_set.append(name)
    #continue
    pass
'''



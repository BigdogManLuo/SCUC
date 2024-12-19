import pulp
import cvxpy as cp
import time
import numpy as np

def mps2Cvxpy(mps_file):
    
    print(f"Reading MPS file {mps_file} to create a CVXPY problem...")

    # Read the MPS file using Pulp
    variables,problem = pulp.LpProblem.fromMPS(mps_file)

    var_dict = {}
    constraints = []

    for var in problem.variables():
        var_dict[var.name] = cp.Variable(name=var.name,boolean=(var.cat == pulp.LpInteger))
        
        
        #变量自身上下限约束
        if var.lowBound is not None:
            constraints.append(var_dict[var.name] >= var.lowBound)
        if var.upBound is not None:
            constraints.append(var_dict[var.name] <= var.upBound)
        
    '''
    objective=0
    for var, coeff in problem.objective.items():
        objective+=var_dict[var.name] * coeff
    objective = cp.Minimize(objective)
    '''
    
    coeff_list = np.array([coeff for var, coeff in problem.objective.items()])
    var_list = [var_dict[var.name] for var, coeff in problem.objective.items()]
    coeff_list = coeff_list.reshape(-1, 1)  # 转换为列向量形状 (n, 1)
    objective = cp.Minimize(cp.sum(cp.multiply(coeff_list, cp.vstack(var_list))))
    

    for constraint in problem.constraints.values():
        lhs = sum(var_dict[var.name] * coeff for var, coeff in constraint.items())
        cons = constraint.constant
        if constraint.sense == pulp.LpConstraintLE:
            constraints.append(lhs+cons <=0 )
        elif constraint.sense == pulp.LpConstraintGE:
            constraints.append(lhs+cons >=0 )
        elif constraint.sense == pulp.LpConstraintEQ:
            constraints.append(lhs+cons ==0 )

    cvxpy_problem = cp.Problem(objective, constraints)

    return cvxpy_problem

def solveProblem(problem):

    print("Solving problem ...")
    start=time.time()
    solver_args={'MIPGap': 1e-2}
    problem.solve(solver=cp.GUROBI,**solver_args)
    end=time.time()
    print(f"Optimal value: {problem.value}",f"Time:{end-start} s")

    return problem

if __name__ == '__main__':

    mps_file = 'data/uccase8.mps'
    cvxpy_problem = mps2Cvxpy(mps_file)
    problem=solveProblem(cvxpy_problem)




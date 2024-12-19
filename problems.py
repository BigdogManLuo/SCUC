import cvxpy as cp
import numpy as np
import pandas as pd
import visualization as vis
import time

T=48
delta_t=0.5 #hour
J=14 #number of ships
S=5 #number of scenarios

#Energy Storage
c_ES=10 #Cost of Energy Storage ($/MWh)
P_ES_max=1.5 #  (MW)
P_ES_min=0 #  (MW)
E_max=5 #MWh
E_min=0  #MWh
eff_ES_ch=0.9 #Charging Efficiency
eff_ES_dch=0.9 #Discharging Effciency

#Grid Power
P_grid_max=7 #MW
G_grid_max=5 #km^3
c_grid_power=pd.read_csv("data/ElectricityPrice.csv")["price"].values #($/MWh)
c_grid_gas=370 #($/km^3)

#Gas Turbine
G_GT_max=3 #km^3
eff_G2E_GT=0.22*10 #Gas to Electric Efficiency
eff_G2H_GT=0.48*10 #Gas to Heat Efficiency
c_GT=4.5 # $/km^3

#Gas Boiler
G_GB_max=0.9 #km^3
eff_G2H_GB=0.7*10 #Gas to Heat Efficiency
c_GB=6.5 #$/km^3

#Electric Boiler
P_EB_max=3 #MW
eff_E2H_EB=0.98 #Electric to Heat Efficiency
c_EB=2.5 #Cost of Electric Boiler ($/MWh)


#PV 
PV_table=pd.read_csv("data/PV.csv")
Pv_pred=PV_table.drop(["true(MW)"],axis=1).values   #MW
Pv_true=PV_table["true(MW)"].values #MW


#Heat Load
H_load_table=pd.read_csv("data/HeatLoad.csv")
H_load_pred=H_load_table.drop(["true(MW)"],axis=1).values   #MW
H_load_true=H_load_table["true(MW)"].values #MW


#Power Load
P_load_table=pd.read_csv("data/PowerLoad.csv")
P_load_pred=P_load_table.drop(["true(MW)"],axis=1).values   #MW
P_load_true=P_load_table["true(MW)"].values #MW

#Gas Load
G_load_table=pd.read_csv("data/GasLoad.csv")
G_load_pred=G_load_table.drop(["true(km3)"],axis=1).values   #km^3
G_load_true=G_load_table["true(km3)"].values #km^3


#Logistic System
t_arrival=pd.read_csv("data/LogisticSystem.csv")["arrival_time"].values 
t_max_leave=pd.read_csv("data/LogisticSystem.csv")["max_leave_time"].values
N_cargo=pd.read_csv("data/LogisticSystem.csv")["cargo_volume"].values #containers
N_qc=7 #number of total quay cranes
P_qc_rated=0.32 #MW
eff_qc=35 #containers/hour
C_qc_max=pd.read_csv("data/LogisticSystem.csv")["max_quay_crane"].values
C_qc_min=pd.read_csv("data/LogisticSystem.csv")["min_quay_crane"].values
P_ship_base=pd.read_csv("data/LogisticSystem.csv")["base_power_load"].values
M=5000 #big M
L_total=500 #m total length of the port
length_ship=pd.read_csv("data/LogisticSystem.csv")["length"].values #m length of ship 

#Carbon
e_power_grid=1.3 #TCO2/MWh
e_gas_grid=2#TCO2/km^3
price_carbon=7 #$/tonCO2
E_allowed=4 #tonCO2

#Stochastic Optimization
propabilities=[0.333,0.321,0.087,0.13,0.129]

def defineDayaheadProblem():
    
    #---------------------------Input Parameters----------------------#
    Pv_pred=cp.Parameter((T,S))
    P_load_pred=cp.Parameter((T,S))
    H_load_pred=cp.Parameter((T,S))
    G_load_pred=cp.Parameter((T,S))

    #---------------------------Variables-----------------------------#
    
    #Power
    P_pv=cp.Variable((S,T))
    P_grid=cp.Variable((S,T))
    P_GT=cp.Variable((S,T))
    P_EB=cp.Variable((S,T))
    P_BES_ch=cp.Variable(T)
    P_BES_dch=cp.Variable(T)
    E_BES=cp.Variable(T+1)
    
    #Gas
    G_grid=cp.Variable((S,T))
    G_GT=cp.Variable((S,T))
    G_GB=cp.Variable((S,T))

    
    #Heat
    H_GT=cp.Variable((S,T))
    H_EB=cp.Variable((S,T))
    H_GB=cp.Variable((S,T))


    #Cost
    C_ES=cp.Variable(T)
    C_EB=cp.Variable((S,T))
    C_GT=cp.Variable((S,T))
    C_GB=cp.Variable((S,T))
    C_grid_power=cp.Variable((S,T))
    C_grid_gas=cp.Variable((S,T))
    C_carbon_IES=cp.Variable((S,T))
    C_carbon_port=cp.Variable(T)

    #Carbon
    E_power_grid_IES=cp.Variable((S,T))
    E_power_grid_port=cp.Variable(T)
    E_gas_grid=cp.Variable((S,T))

    #Port Logistic System
    X=cp.Variable((J,T), boolean=True) #staus of in-port for ship j at time t
    t_in=cp.Variable(J) #arrival time
    t_leave=cp.Variable(J) #leave time
    u=cp.Variable(J, boolean=True) #auxiliary variable
    v=cp.Variable(J, boolean=True) #auxiliary variable
    y_1=cp.Variable((J,T), boolean=True) #auxiliary variable
    y_2=cp.Variable((J,T), boolean=True) #auxiliary variable
    y_3=cp.Variable((J,T), boolean=True) #auxiliary variable
    W=cp.Variable((J,T), boolean=True) #auxiliary variable
    C_qc={k:cp.Variable((J,T), boolean=True) for k in range(N_qc)}
    P_crane=cp.Variable(T) #power consumption of quay crane at time t
    P_shore=cp.Variable(T) #power consumption of shore at time t
    b=cp.Variable(J) #location of ship j
    z=cp.Variable((J,J), boolean=True) #船舶i的离港时间比船舶j的靠泊时间早
    h=cp.Variable((J,J), boolean=True) #船舶i在船舶j得左侧靠泊
    
    #----------------------Constraints----------------------------#
    constraints_IES=[]
    constraints_Port=[]
    constraints_public=[]

    #Energy Storage Constraints
    constraints_IES+=[E_BES[0]==0.5*E_max]
    constraints_IES+=[E_BES[T]==0.5*E_max]
    for t in range(T):

        constraints_IES+=[E_BES[t+1]==E_BES[t]+P_BES_ch[t]*eff_ES_ch*delta_t-delta_t*(P_BES_dch[t]/eff_ES_dch)]
        constraints_IES+=[C_ES[t]==(P_BES_ch[t]+P_BES_dch[t])*delta_t*c_ES] #cost
        constraints_IES+=[P_BES_ch[t]<=P_ES_max]
        constraints_IES+=[P_BES_ch[t]>=P_ES_min]
        constraints_IES+=[P_BES_dch[t]<=P_ES_max]
        constraints_IES+=[P_BES_dch[t]>=P_ES_min]
        constraints_IES+=[E_BES[t]<=E_max]
        constraints_IES+=[E_BES[t]>=E_min]
        
    #Photovolatic Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[P_pv[s,t]>=0]
            constraints_IES+=[P_pv[s,t]<=Pv_pred[t,s]]
        
    #Grid Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[P_grid[s,t]>=0]
            constraints_IES+=[P_grid[s,t]<=P_grid_max]
            constraints_IES+=[G_grid[s,t]>=0]
            constraints_IES+=[G_grid[s,t]<=G_grid_max]
            constraints_IES+=[C_grid_power[s,t]==P_grid[s,t]*c_grid_power[t]*delta_t] #power purchase cost
            constraints_IES+=[C_grid_gas[s,t]==G_grid[s,t]*c_grid_gas*delta_t] #gas purchase cost

    #Gas Turbine Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[G_GT[s,t]>=0]
            constraints_IES+=[G_GT[s,t]<=G_GT_max]
            constraints_IES+=[P_GT[s,t]==G_GT[s,t]*eff_G2E_GT] # gas2elec
            constraints_IES+=[H_GT[s,t]==G_GT[s,t]*eff_G2H_GT] # gas2heat
            constraints_IES+=[C_GT[s,t]==G_GT[s,t]*c_GT*delta_t] #cost

    #Gas Boiler Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[G_GB[s,t]>=0]
            constraints_IES+=[G_GB[s,t]<=G_GB_max]
            constraints_IES+=[H_GB[s,t]==G_GB[s,t]*eff_G2H_GB]
            constraints_IES+=[C_GB[s,t]==G_GB[s,t]*c_GB*delta_t] #cost


    #Electric Boiler Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[P_EB[s,t]>=0]
            constraints_IES+=[P_EB[s,t]<=P_EB_max]
            constraints_IES+=[H_EB[s,t]==P_EB[s,t]*eff_E2H_EB] # elec2heat
            constraints_IES+=[C_EB[s,t]==P_EB[s,t]*c_EB*delta_t] #cost


    #In-Port time Constraints
    for j in range(J):

        #In-Port time and leave time constraints
        constraints_Port+=[t_in[j]>=t_arrival[j]]
        constraints_Port+=[t_in[j]<=T]
        
        constraints_Port+=[t_leave[j]>=t_in[j]+N_cargo[j]/(delta_t*eff_qc*C_qc_max[j])]
        constraints_Port+=[t_leave[j]<=t_max_leave[j]]
        
        constraints_Port+=[t_leave[j]<=t_in[j]+N_cargo[j]/(delta_t*eff_qc*C_qc_min[j])]
        constraints_Port+=[t_leave[j]>=t_max_leave[j]-M*(1-u[j])]
        constraints_Port+=[t_leave[j]<=t_max_leave[j]-M*(1-v[j])]
        constraints_Port+=[u[j]+v[j]>=1]
         
    # In-Port and leave status
    for j in range(J):
        for t in range(T):
            #big-M
            constraints_Port+=[X[j,t]==y_2[j,t]]
            constraints_Port+=[y_1[j,t]+y_2[j,t]+y_3[j,t]==1]
            constraints_Port+=[t_in[j]>=t-M*(1-y_1[j,t])]
            constraints_Port+=[t_leave[j]>=t-M*(1-y_2[j,t])]
            constraints_Port+=[t>=t_in[j]-M*(1-y_2[j,t])]
            constraints_Port+=[t>=t_leave[j]-M*(1-y_3[j,t])]
            
            #only arrival 1 time
            if t<T-1:
                constraints_Port+=[X[j,t]>=X[j,t+1]-W[j,t]]
                constraints_Port+=[W[j,t]<=X[j,t+1]]
                constraints_Port+=[W[j,t]<=y_1[j,t]]
                constraints_Port+=[W[j,t]>=X[j,t+1]+y_1[j,t]-1]
    
    # Quay Crane Constraints
    for t in range(T):
        for j in range(J):  
            constraints_Port+=[sum(C_qc[k][j,t] for k in range(N_qc))>=C_qc_min[j]*X[j,t]] 
            constraints_Port+=[sum(C_qc[k][j,t] for k in range(N_qc))<=C_qc_max[j]*X[j,t]]
        #constraints_Port+=[sum(C_qc[k] cp.sum([:,t] for k in range(N_qc))<=N_qc] 

        #每一岸桥在同一时间段内只服务于一艘船舶
        for k in range(N_qc):
            constraints_Port+=[cp.sum(C_qc[k][:,t])<=1] 
        
        #岸桥工作连续性
        for j in range(J):  
            for k in range(1,N_qc-1):
                constraints_Port+= [C_qc[k+1][j,t]+C_qc[k-1][j,t]-C_qc[k][j,t]<=1]
    
    #泊位调度
    for i in range(J):
        constraints_Port+=[b[i]+length_ship[i]<=L_total]
        constraints_Port+=[b[i]>=0]
        
        for j in range(J):
            if i!=j:
                constraints_Port+=[b[i]+length_ship[i]<=b[j]+M*(1-h[i,j])]
                constraints_Port+=[t_leave[i]<=t_in[j]+M*(1-z[i,j])]
                constraints_Port+=[h[i,j]+h[j,i]+z[i,j]+z[j,i]>=1]


    #Quay Crane Load
    for t in range(T):
        constraints_Port+=[P_crane[t]==sum(cp.sum(C_qc[k][:,t]) for k in range(N_qc))*P_qc_rated]


    #Shore Power Load
    for t in range(T):
        constraints_Port+=[P_shore[t]==sum(P_ship_base[j]*X[j,t] for j in range(J))]
    

    #Heat Balance Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[H_GT[s,t]+H_EB[s,t]+H_GB[s,t]==H_load_pred[t,s]]


    #Gas Balance Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[G_grid[s,t]==G_GT[s,t]+G_GB[s,t]+G_load_pred[t,s]]


    #Power Balance Constraints
    for s in range(S):
        for t in range(T):
            constraints_public+=[P_grid[s,t]+P_GT[s,t]+P_BES_dch[t]-P_BES_ch[t]+P_pv[s,t]==P_load_pred[t,s]+P_EB[s,t]+P_crane[t]+P_shore[t]]
    
    #Carbon Constraints
    for s in range(S):
        for t in range(T):
            constraints_IES+=[E_power_grid_IES[s,t]==(P_load_pred[t,s]+P_EB[s,t]+P_BES_ch[t]-P_BES_dch[t]-P_pv[s,t]-P_GT[s,t])*e_power_grid*delta_t]
            constraints_Port+=[E_power_grid_port[t]==(P_crane[t]+P_shore[t])*e_power_grid*delta_t]
            constraints_IES+=[E_gas_grid[s,t]==G_grid[s,t]*e_gas_grid*delta_t]
            constraints_IES+=[C_carbon_IES[s,t]==(E_power_grid_IES[s,t]+E_gas_grid[s,t])*price_carbon]
            constraints_Port+=[C_carbon_port[t]==E_power_grid_port[t]*price_carbon]
            
    #----------------------Objective Function----------------------------#
    #目标函数做一个区分
    obj_IES= sum(propabilities[s]*(
        cp.sum(C_EB[s])+cp.sum(C_GT[s])+cp.sum(C_GB[s])+cp.sum(C_grid_gas[s])+c_grid_power@(P_load_pred[:,s]+P_EB[s]+P_BES_ch-P_BES_dch-P_pv[s]-P_GT[s]) + cp.sum(C_carbon_IES[s])
        )
        for s in range(S)) + cp.sum(C_ES)
    
    obj_Port=c_grid_power@(P_crane+P_shore)+cp.sum(C_carbon_port)
    
    obj=sum(propabilities[s]*(
        cp.sum(C_EB[s])+cp.sum(C_GT[s])+cp.sum(C_GB[s])+cp.sum(C_grid_gas[s])+cp.sum(C_grid_power[s]) + cp.sum(C_carbon_IES[s])
        )
        for s in range(S)) + cp.sum(C_ES) +cp.sum(C_carbon_port)
    
    #----------------------Solve the problem----------------------------#
    prob=cp.Problem(cp.Minimize(obj),constraints_IES+constraints_Port+constraints_public)
    
    variables_IES={
        "P_pv":P_pv,
        "P_BES_ch":P_BES_ch,
        "P_BES_dch":P_BES_dch,
        "E_BES":E_BES,
        "P_grid":P_grid,
        "P_GT":P_GT,
        "P_EB":P_EB,
        "G_grid":G_grid,
        "G_GT":G_GT,
        "G_GB":G_GB,
        "H_GT":H_GT,
        "H_EB":H_EB,
        "H_GB":H_GB,
        "C_ES":C_ES,
        "C_EB":C_EB,
        "C_GT":C_GT,
        "C_GB":C_GB,
        "C_grid_power":C_grid_power,
        "C_grid_gas":C_grid_gas,
        "C_carbon_IES":C_carbon_IES,
        "E_power_grid_IES":E_power_grid_IES,
        "E_gas_grid":E_gas_grid
    }

    variables_Port={
        "X":X,
        "t_in":t_in,
        "t_leave":t_leave,
        "y_1":y_1,
        "y_2":y_2,
        "y_3":y_3,
        "W":W,
        "C_qc":C_qc,
        "P_crane":P_crane,
        "P_shore":P_shore,
        "b":b,
        "z":z,
        "h":h,
        "C_carbon_port":C_carbon_port,
        "E_power_grid_port":E_power_grid_port

    }

    #合并两个字典为variables
    variables={**variables_IES,**variables_Port}
    
    parameters={
        "Pv_pred":Pv_pred,
        "P_load_pred":P_load_pred,
        "H_load_pred":H_load_pred,
        "G_load_pred":G_load_pred
    }

    return prob,parameters,variables,variables_IES,variables_Port,obj_IES,obj_Port,constraints_IES,constraints_Port,constraints_public


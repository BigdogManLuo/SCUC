import pandas as pd
import cvxpy as cp
import numpy as np
import utils
import coptpy as copt


def calculateCosts(P_ES_ch,P_ES_dch,U_ch,U_dch,P_unit,U_unit,):

    eps=0.1
    #充电成本
    Cost_ES_ch=stbidprice[0]*np.sum(U_ch)

    #放电成本
    Cost_ES_dch=0
    for t in range(24):
        
        #判断P_ES_dch属于哪一段
        flag=0
        if P_ES_dch[t]!=0:
            for j in range(N_ES_segs):
                if P_ES_dch[t]>=P_ES_mins[j] and P_ES_dch[t]<=P_ES_maxs[j]:
                    flag=1
                    break
            if flag==0:
                raise ValueError('P_ES_dch[t]不在任何一段范围内')

            Cost_ES_dch+=a_ES[j]*P_ES_dch[t]+b_ES[j]
            
        else:
            Cost_ES_dch+=0
        

    #通过Unit推导启动和停机的indicator
    V_unit=np.zeros_like(U_unit)
    W_unit=np.zeros_like(U_unit)

    for i in range(U_unit.shape[0]):
        for t in range(24):
            if t==0: #初始时刻的启停机状态
                V_unit[i,t]=max(0,U_unit[i,t]-unitdata['初始状态(1开机,0停机)'][i])
                W_unit[i,t]=max(0,unitdata['初始状态(1开机,0停机)'][i]-U_unit[i,t])

            if t>0:
                V_unit[i,t]=max(0,U_unit[i,t]-U_unit[i,t-1])
                W_unit[i,t]=max(0,U_unit[i,t-1]-U_unit[i,t])

    #机组启动成本
    Cost_unit_start=0
    for t in range(24):
        Cost_unit_start+=sum(unitdata['启动成本（元）'][i]*V_unit[i,t] for i in range(U_unit.shape[0]))


    #机组运行成本
    Cost_unit_opr=0
    for t in range(24):
        for i in range(P_unit.shape[0]):


            #计算成本区间上下限
            P_unit_mins,P_unit_maxs=utils.getSegmentedPoints(num_seg=N_unit_segs,deltaP=bid_capacity.iloc[i,1],P_min=unitdata['最小出力(MW)'][i])

            #每个区间的斜率和截距
            a_unit,b_unit=utils.getSegmentedCostInfo(prices=bid_price.iloc[i,2:],deltaP=bid_capacity.iloc[i,1],P_min=unitdata['最小出力(MW)'][i])

            #判断P_unit[i,t]属于哪一段
            flag=0
            if P_unit[i,t]!=0:
                for j in range(bid_capacity.shape[1]-1):
                    if P_unit[i,t]>=P_unit_mins[j]-eps and P_unit[i,t]<=P_unit_maxs[j]+eps:
                        flag=1
                        break
                    
                if flag==0:
                    raise ValueError('P_unit[i,t]不在任何一段范围内')
                
                Cost_unit_opr+=a_unit[j]*P_unit[i,t]+b_unit[j]*U_unit[i,t]
            else:
                Cost_unit_opr+=0


    return Cost_ES_ch,Cost_ES_dch,Cost_unit_start,Cost_unit_opr


#%%  
instance_num=100

#---------------------------Parameters-----------------------------------------#
bid_capacity = utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/bidcapacity.txt'))
bid_price= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/bidprice.txt'))
section= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/section.txt'))
load= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/slf.txt'))
stbidcapactiy= utils.readStorageBidInfo(f'data/instances/{instance_num}/stbidcapacity.txt')
stbidprice= utils.readStorageBidInfo(f'data/instances/{instance_num}/stbidprice.txt')
storagebasic= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/storagebasic.txt'))
unitdata= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/unitdata.txt'))
gen_senses,load_sense,branch=utils.parse_log_file(f'data/instances/{instance_num}/branch_1.log')


M=100000 #大M法中的大M值
T=24 
#-----------------------火电信息------------------------------
N_units=unitdata.shape[0]
N_unit_segs=bid_capacity.shape[1]-1

#计算火电的分段斜率
a_unit=np.zeros((N_units,N_unit_segs))
b_unit=np.zeros((N_units,N_unit_segs))
deltaP_unit=bid_capacity.iloc[:,1]
for i in range(N_units):
    a_unit[i],b_unit[i]=utils.getSegmentedCostInfo(prices=bid_price.iloc[i,2:],deltaP=deltaP_unit[i],P_min=unitdata['最小出力(MW)'][i])
C0_unit=bid_price['第一段价格(元)']

#----------------------储能分段线性信息---------------------------
deltaP_ES=stbidcapactiy[1] #储能分段功率的间隔
N_ES_segs=len(stbidcapactiy)-2
N_ESs=storagebasic.shape[0]
a_ES,b_ES=utils.getSegmentedCostInfo(stbidprice[2:],deltaP=deltaP_ES,P_min=storagebasic['最小发电功率（MW）'][0]) #储能成本分段线性化
P_ES_mins,P_ES_maxs=utils.getSegmentedPoints(num_seg=N_ES_segs,deltaP=stbidcapactiy[1],P_min=storagebasic['最小发电功率（MW）'][0]) #储能分段功率的上下限
C0_ES=stbidprice[2]


#---------------------断面信息-------------------------
restricted_branches = section['断面组成']
N_restricted_branches=len(restricted_branches)
PF_load=np.zeros((N_restricted_branches,T)) #负荷对断面的潮流

#计算每个时刻每个断面的负荷潮流
for t in range(T):
    for j in range(N_restricted_branches):
        
        #找到对应的断面在load_sense中的部分
        load_in_branch=load_sense[load_sense['支路名称（ID）']==restricted_branches[j]].reset_index(drop=True)
        
        #负荷对断面的潮流
        PF_load[j,t]=load_in_branch['母线负荷对该支路潮流的灵敏度值乘积和'][t]


#%%   建模
env = copt.Envr() 
model = env.createModel() 

#---------------------------Variables-----------------------------#
#Unit Data
P_unit=model.addVars(N_units,T,nameprefix='P_unit')
U_unit=model.addVars(N_units,T,vtype=copt.COPT.BINARY,nameprefix='U_unit') #开停机state
V_unit=model.addVars(N_units,T,vtype=copt.COPT.BINARY,nameprefix='V_unit') #启动indicator
W_unit=model.addVars(N_units,T,vtype=copt.COPT.BINARY,nameprefix='W_unit') #停机indicator
P_unit_segs=model.addVars(N_unit_segs,N_units,T,nameprefix='P_unit_segs') #火电机组分段功率
PF_unit=model.addVars(N_restricted_branches,T,nameprefix='PF_unit',lb=-1000000000) #火电机组对断面的潮流
Cost_unit_start=model.addVars(N_units,T,nameprefix='Cost_unit_start')
Cost_unit_opr=model.addVars(N_units,T,nameprefix='Cost_unit_opr')

#Storage Data
U_ch=model.addVars(N_ESs,T,vtype=copt.COPT.BINARY,nameprefix='U_ch') #充电state
U_dch=model.addVars(N_ESs,T,vtype=copt.COPT.BINARY,nameprefix='U_dch') #放电state
U_ES=model.addVars(N_ESs,T,vtype=copt.COPT.BINARY,nameprefix='U_ES') #停机state
Z_ch=model.addVars(N_ESs,T,vtype=copt.COPT.BINARY,nameprefix='Z_ch') #充电indicator
Z_dch=model.addVars(N_ESs,T,vtype=copt.COPT.BINARY,nameprefix='Z_dch') #放电indicator
Z_ES=model.addVars(N_ESs,T,vtype=copt.COPT.BINARY,nameprefix='Z_ES') #停机indicator
P_ES_ch=model.addVars(N_ESs,T,nameprefix='P_ES_ch') #充电功率
P_ES_dch=model.addVars(N_ESs,T,nameprefix='P_ES_dch') #放电功率
P_ES_dch_segs=model.addVars(N_ES_segs,N_ESs,T,nameprefix='P_ES_dch_segs') #储能机组分段功率
PF_ES=model.addVars(N_restricted_branches,T,nameprefix='PF_ES',lb=-100000000) #储能机组对断面的潮流
ES=model.addVars(N_ESs,T+1,nameprefix='ES') #储能容量剩余
Cost_ES_ch=model.addVars(N_ESs,T,nameprefix='Cost_ES_ch',lb=-100000000) #储能充电成本
Cost_ES_dch=model.addVars(N_ESs,T,nameprefix='Cost_ES_dch') #储能放电成本


#---------------------------Constraints-----------------------------#
constraints=[]

#火电机组约束
for i in range(N_units):

    for t in range(T):

        #发电功率上下限约束
        model.addConstr(P_unit[i,t]<=unitdata['最大出力(MW)'][i]*U_unit[i,t])
        model.addConstr(P_unit[i,t]>=unitdata['最小出力(MW)'][i]*U_unit[i,t])

        #最小开机时间约束
        if unitdata['初始状态(1开机,0停机)'][i]==1: #如果初始状态为开机
            if unitdata['初始状态持续时间(h)'][i]-unitdata['最小开机时间(h)'][i]+t<0: #初始状态持续时间小于最小开机时间,则需要继续保持初始状态
                model.addConstr(U_unit[i,t]==1)
        
        if t+unitdata['最小开机时间(h)'][i]<=T:
            model.addConstr(sum([U_unit[i,k] for k in range(t,t+unitdata['最小开机时间(h)'][i])])>=unitdata['最小开机时间(h)'][i]*V_unit[i,t])
        else:
            model.addConstr(sum([U_unit[i,k] for k in range(t,T)])>=V_unit[i,t]*(T-t))

        
        #最小停机时间约束
        if unitdata['初始状态(1开机,0停机)'][i]==0:    #如果初始状态为停机
            if unitdata['初始状态持续时间(h)'][i]-unitdata['最小停机时间(h)'][i]+t<0: #初始状态持续时间小于最小停机时间,则需要继续保持初始状态
                model.addConstr(U_unit[i,t]==0)
        
        if t+unitdata['最小停机时间(h)'][i]<=T:
            model.addConstr(sum([1-U_unit[i,k] for k in range(t,t+unitdata['最小停机时间(h)'][i])])>=unitdata['最小停机时间(h)'][i]*W_unit[i,t])
        else:
            model.addConstr(sum([1-U_unit[i,k] for k in range(t,T)])>=W_unit[i,t]*(T-t))
        
        #启停机状态转换
        if t==0: #初始时刻的启停机状态

            model.addConstr(V_unit[i,t]>=U_unit[i,t]-unitdata['初始状态(1开机,0停机)'][i])
            model.addConstr(V_unit[i,t]<=1-unitdata['初始状态(1开机,0停机)'][i])
            model.addConstr(V_unit[i,t]<=U_unit[i,t])
            
            model.addConstr(W_unit[i,t]>=unitdata['初始状态(1开机,0停机)'][i]-U_unit[i,t])
            model.addConstr(W_unit[i,t]<=1-U_unit[i,t])
            model.addConstr(W_unit[i,t]<=unitdata['初始状态(1开机,0停机)'][i])

        
        if t>0:

            model.addConstr(V_unit[i,t]>=U_unit[i,t]-U_unit[i,t-1])
            model.addConstr(V_unit[i,t]<=1-U_unit[i,t-1])
            model.addConstr(V_unit[i,t]<=U_unit[i,t])
            
            model.addConstr(W_unit[i,t]>=U_unit[i,t-1]-U_unit[i,t])
            model.addConstr(W_unit[i,t]<=1-U_unit[i,t])
            model.addConstr(W_unit[i,t]<=U_unit[i,t-1])

    
        #爬坡率约束 （开停机动作可以不满足爬坡率约束）
        if t==0: 
            model.addConstr(P_unit[i,t]-unitdata['初始出力(MW)'][i]<=unitdata['上爬坡率(MW/h)'][i]+M*(V_unit[i,t]))
            model.addConstr(unitdata['初始出力(MW)'][i]-P_unit[i,t]<=unitdata['下爬坡率(MW/h)'][i]+M*(W_unit[i,t]))
        
        elif t>0:
            model.addConstr(P_unit[i,t]-P_unit[i,t-1]<=unitdata['上爬坡率(MW/h)'][i]+M*(V_unit[i,t]))
            model.addConstr(P_unit[i,t-1]-P_unit[i,t]<=unitdata['下爬坡率(MW/h)'][i]+M*(W_unit[i,t]))
        
        #启动成本
        model.addConstr(Cost_unit_start[i,t]==unitdata['启动成本（元）'][i]*V_unit[i,t])
        
        #仅调试
        #model.addConstr(Cost_unit_opr[i,t]==np.mean(a_unit[i])*P_unit[i,t]+np.mean(b_unit[i])*U_unit[i,t])
        
        
        #运行成本分段线性化
        for j in range(N_unit_segs):
            
            model.addConstr(P_unit_segs[j,i,t]>=0)
            model.addConstr(P_unit_segs[j,i,t]<=deltaP_unit[i])

        #每段功率之和等于总功率
        model.addConstr(P_unit[i,t]==sum([P_unit_segs[j,i,t] for j in range(N_unit_segs)])+unitdata['最小出力(MW)'][i]*U_unit[i,t])
            
        #总成本
        model.addConstr(Cost_unit_opr[i,t]==sum(a_unit[i][j]*P_unit_segs[j,i,t] for j in range(N_unit_segs))+U_unit[i,t]*C0_unit[i])
        

#储能约束
for i in range(N_ESs):

    # 初始容量
    model.addConstr(ES[i, 0] == storagebasic['初始容量（MWh）'][i])
    
    # 终止容量
    model.addConstr(ES[i, T] >= storagebasic['终止容量（MWh）'][i])

    for t in range(T):

        #充电功率约束
        model.addConstr(P_ES_ch[i, t] == storagebasic['抽水固定功率（MW）'][i] * U_ch[i, t])
        
        #放电功率约束
        model.addConstr(P_ES_dch[i, t] >= storagebasic['最小发电功率（MW）'][i]* U_dch[i, t])
        model.addConstr(P_ES_dch[i, t] <=storagebasic['最大发电功率（MW）'][i]* U_dch[i, t])
        
        #储能容量约束
        model.addConstr(ES[i, t+1] == ES[i, t] + P_ES_ch[i, t] - P_ES_dch[i, t])
        model.addConstr(ES[i, t] <= storagebasic['最大容量（MWh）'][i])
        model.addConstr(ES[i, t] >= 0) 

        #最小抽水时间约束
        if t+storagebasic['最小抽水时段'][i]<=T:
            model.addConstr(sum([U_ch[i, k] for k in range(t, t + storagebasic['最小抽水时段'][i])]) >= storagebasic['最小抽水时段'][i] * Z_ch[i, t])
        else:
            model.addConstr(sum([U_ch[i, k] for k in range(t, T)]) >= Z_ch[i, t] * (T - t))

        #最小放电时间约束
        if t+storagebasic['最小发电时段'][i]<=T:
            model.addConstr(sum([U_dch[i, k] for k in range(t, t + storagebasic['最小发电时段'][i])]) >= storagebasic['最小发电时段'][i] * Z_dch[i, t])
        else:
            model.addConstr(sum([U_dch[i, k] for k in range(t, T)]) >= Z_dch[i, t] * (T - t))

        #最小停机时间约束
        if t+storagebasic['最小停机时段'][i]<=T:
            model.addConstr(sum([U_ES[i, k] for k in range(t, t + storagebasic['最小停机时段'][i])]) >= storagebasic['最小停机时段'][i] * Z_ES[i, t])
        else:
            model.addConstr(sum([U_ES[i, k] for k in range(t, T)]) >= Z_ES[i, t] * (T - t))

        #状态互斥约束
        model.addConstr(U_ch[i, t] + U_dch[i, t] + U_ES[i, t] == 1)

        #状态转换约束
        if t==0:
            model.addConstr(Z_dch[i, t] == U_dch[i, t]-0) #如果第一时刻选择放电，则放电indicator激活
            model.addConstr(Z_ch[i, t] == U_ch[i, t]-0)  #如果第一时刻选择充电，则充电indicator激活
            model.addConstr(Z_ES[i, t] == 0) #第一时刻停机也不会激活停机indicator
            
        if t > 0:
            model.addConstr(Z_ch[i, t] >= U_ch[i, t] - U_ch[i, t - 1])
            model.addConstr(Z_ch[i, t] <= 1 - U_ch[i, t - 1])
            model.addConstr(Z_ch[i, t] <= U_ch[i, t])

            model.addConstr(Z_dch[i, t] >= U_dch[i, t] - U_dch[i, t - 1])
            model.addConstr(Z_dch[i, t] <= 1-U_dch[i, t - 1])
            model.addConstr(Z_dch[i, t] <= U_dch[i, t])

            model.addConstr(Z_ES[i, t] >= U_ES[i, t] - U_ES[i, t - 1])
            model.addConstr(Z_ES[i, t] <= 1 - U_ES[i, t - 1])
            model.addConstr(Z_ES[i, t] <= U_ES[i, t])

            #状态切换，充电状态与发电状态相互的切换必须经过停机状态
            model.addConstr(Z_dch[i, t] <= U_ES[i, t - 1])
            model.addConstr(Z_ch[i, t] <= U_ES[i, t - 1])

        #充电成本
        model.addConstr(Cost_ES_ch[i,t]==stbidprice[0]*U_ch[i,t])
        
        
        #放电成本分段线性化
        for j in range(N_ES_segs):
            model.addConstr(P_ES_dch_segs[j,i,t]>=0)
            model.addConstr(P_ES_dch_segs[j,i,t]<=deltaP_ES)

        #每段功率之和等于总功率
        model.addConstr(P_ES_dch[i,t]==sum([P_ES_dch_segs[j,i,t] for j in range(N_ES_segs)])+storagebasic['最小发电功率（MW）'][i]*U_dch[i,t])

        #总成本
        model.addConstr(Cost_ES_dch[i,t]==sum(a_ES[j]*P_ES_dch_segs[j,i,t] for j in range(N_ES_segs))+U_dch[i,t]*C0_ES)

#系统约束
for t in range(T):

    #系统平衡约束
    model.addConstr(copt.quicksum(P_unit[i, t] for i in range(N_units))
                    +copt.quicksum(P_ES_dch[i, t] for i in range(N_ESs))
                    -copt.quicksum(P_ES_ch[i, t] for i in range(N_ESs))==load['系统负荷大小（MW）'][t])
    
    #系统备用约束
    model.addConstr(copt.quicksum(U_unit[i,t]*unitdata['最大出力(MW)'][i]-P_unit[i, t] for i in range(N_units)) >= 0.1*load['系统负荷大小（MW）'][t])
    
    
    #断面约束
    for j in range(N_restricted_branches):

        #找到对应的断面在gen_senses中的位置
        branch_idx=gen_senses[gen_senses['支路中文名']==restricted_branches[j]].index[0]
    
        model.addConstr(PF_unit[j,t]==copt.quicksum(P_unit[i,t]*gen_senses[f'{i+1}对所列支路潮流的灵敏度值'][branch_idx] for i in range(N_units)))

        #储能机组对断面的潮流
        model.addConstr(PF_ES[j,t]==copt.quicksum((P_ES_dch[i,t]-P_ES_ch[i,t])*gen_senses[f'{len(unitdata)}对所列支路潮流的灵敏度值'][branch_idx] for i in range(N_ESs)))

        #断面潮流约束
        model.addConstr(PF_unit[j,t]+PF_ES[j,t]-PF_load[j,t]<=section['断面限额'][j])

#---------------------------------Objective---------------------------------#
#目标函数=火电机组的启动成本+火电机组的运行成本+储能机组的运行成本
                  
model.setObjective(copt.quicksum(Cost_unit_start)+copt.quicksum(Cost_unit_opr)+copt.quicksum(Cost_ES_ch)+copt.quicksum(Cost_ES_dch), 
                   sense=copt.COPT.MINIMIZE)

#---------------------------------Solve---------------------------------#
model.setParam("Logging", 1)
model.setParam("RelGap", 5e-4)
model.solve()
if model.status == copt.COPT.INFEASIBLE:
  # Compute IIS
  model.computeIIS()
  model.writeIIS('iis_ex1.iis')


#整理变量
P_unit_val=np.array([[P_unit[i,t].value for t in range(T)] for i in range(N_units)])
U_unit_val=np.array([[U_unit[i,t].value for t in range(T)] for i in range(N_units)])
U_ch_val=np.array([[U_ch[i,t].value for t in range(T)] for i in range(N_ESs)])
U_dch_val=np.array([[U_dch[i,t].value for t in range(T)] for i in range(N_ESs)])
U_ES_val=np.array([[U_ES[i,t].value for t in range(T)] for i in range(N_ESs)])
P_ES_ch_val=np.array([[P_ES_ch[i,t].value for t in range(T)] for i in range(N_ESs)])
P_ES_dch_val=np.array([[P_ES_dch[i,t].value for t in range(T)] for i in range(N_ESs)])


#---------------------------------Output---------------------------------#

#print 成本
print('火电机组启动成本:',copt.quicksum(Cost_unit_start).value)
print('火电机组运行成本:',copt.quicksum(Cost_unit_opr).value)
print('储能机组充电成本:',copt.quicksum(Cost_ES_ch).value)
print('储能机组放电成本:',copt.quicksum(Cost_ES_dch).value)
print('总成本:',model.objval)
print('---------------------------------')

#通过成本函数计算成本
Cost_ES_ch_val,Cost_ES_dch_val,Cost_unit_start_val,Cost_unit_opr_val=calculateCosts(P_ES_ch_val[0],P_ES_dch_val[0],U_ch_val[0],U_dch_val[0],P_unit_val,U_unit_val)
print('校验火电机组启动成本:',Cost_unit_start_val)
print('校验火电机组运行成本:',Cost_unit_opr_val)
print('校验储能机组充电成本:',Cost_ES_ch_val)
print('校验储能机组放电成本:',Cost_ES_dch_val)
print('校验总成本:',Cost_unit_start_val+Cost_unit_opr_val+Cost_ES_ch_val+Cost_ES_dch_val)
print('---------------------------------')


#校验外部最优解对应的成本
Vars=utils.readSols(f'data/instances/{instance_num}/solution.sol')
utils.Sols2Excel(**Vars,instance_num=instance_num,is_opt=True)
Vars.pop('U_ES')
Cost_ES_ch_val,Cost_ES_dch_val,Cost_unit_start_val,Cost_unit_opr_val=calculateCosts(**Vars)
print('外部最优解校验火电机组启动成本:',Cost_unit_start_val)
print('外部最优解校验火电机组运行成本:',Cost_unit_opr_val)
print('外部最优解校验储能机组充电成本:',Cost_ES_ch_val)
print('外部最优解校验储能机组放电成本:',Cost_ES_dch_val)
print('外部最优解校验总成本:',Cost_unit_start_val+Cost_unit_opr_val+Cost_ES_ch_val+Cost_ES_dch_val)

utils.Sols2Excel(U_unit_val,P_unit_val,U_ch_val[0],U_dch_val[0],U_ES_val[0],P_ES_ch_val[0],P_ES_dch_val[0],instance_num=instance_num,is_opt=False)

#写入solution.sol
utils.writeSols(model,U_unit_val,P_unit_val,U_ch_val,U_dch_val,U_ES_val,P_ES_ch_val,P_ES_dch_val,instance_num=instance_num)



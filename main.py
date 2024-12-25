import numpy as np
import utils
import coptpy as copt
import os

def calculateCosts(P_ES_ch,P_ES_dch,U_ch,U_dch,P_unit,U_unit,):

    eps=0.001
    N_ESs=P_ES_ch.shape[0]
    N_ES_segs=stbidcapactiy.shape[1]-3

    #充电成本
    Cost_ES_ch=0
    for i in range(N_ESs):
        Cost_ES_ch+=stbidprice['价格-1'][i]*np.sum(U_ch[i])

    #放电成本
    Cost_ES_dch=0
    for i in range(N_ESs):

        #计算成本区间上下限
        P_ES_mins,P_ES_maxs=utils.getSegmentedPoints(num_seg=N_ES_segs,deltaP=stbidcapactiy['报价段1'][i],P_min=storagebasic['最小发电功率（MW）'][i])

        for t in range(24):
            #判断P_ES_dch属于哪一段
            flag=0
            if abs(P_ES_dch[i,t])>eps:
                for j in range(N_ES_segs):
                    if P_ES_dch[i,t]>=P_ES_mins[j]-eps and P_ES_dch[i,t]<=P_ES_maxs[j]+eps:
                        flag=1
                        break
                if flag==0:
                    raise ValueError('P_ES_dch[i,t]不在任何一段范围内')

                Cost_ES_dch+=a_ES[i][j]*P_ES_dch[i,t]+b_ES[i][j]
                
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
            if abs(P_unit[i,t])>eps:
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
#输入求解的样例编号
instance_num=200 

#---------------------------Parameters-----------------------------------------#
bid_capacity = utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/bidcapacity.txt'))
bid_price= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/bidprice.txt'))
section= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/section.txt'))
load= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/slf.txt'))
stbidcapactiy=utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/stbidcapacity.txt',is_storage_price=True))
stbidprice=utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/stbidprice.txt',is_storage_price=True))
storagebasic= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/storagebasic.txt'))
unitdata= utils.txt_to_dataframe(utils.read_txt(f'data/instances/{instance_num}/unitdata.txt'))
gen_senses,load_sense,branch=utils.parse_log_file(f'data/instances/{instance_num}/branch_1.log')


M=10000 #大M法中的大M值
T=24 
#-----------------------火电信息------------------------------
N_units=unitdata.shape[0]
N_unit_segs=bid_capacity.shape[1]-1

#计算火电的分段斜率
a_unit=np.zeros((N_units,N_unit_segs))
b_unit=np.zeros((N_units,N_unit_segs))
deltaP_unit=bid_capacity['第一段功率(MW)']
for i in range(N_units):
    a_unit[i],b_unit[i]=utils.getSegmentedCostInfo(prices=bid_price.iloc[i,2:],deltaP=deltaP_unit[i],P_min=unitdata['最小出力(MW)'][i])
C0_unit=bid_price['第一段价格(元)']

#----------------------储能信息---------------------------
N_ESs=storagebasic.shape[0]
N_ES_segs=stbidcapactiy.shape[1]-3

#计算储能的分段斜率
a_ES=np.zeros((N_ESs,N_ES_segs))
b_ES=np.zeros((N_ESs,N_ES_segs))
deltaP_ES=stbidcapactiy['报价段1']
for i in range(N_ESs):
    a_ES[i],b_ES[i]=utils.getSegmentedCostInfo(prices=stbidprice.iloc[i,3:],deltaP=deltaP_ES[i],P_min=storagebasic['最小发电功率（MW）'][i])
    
C0_ES=stbidprice['价格1']


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
PF_unit=model.addVars(N_restricted_branches,T,nameprefix='PF_unit',lb=-100000) #火电机组对断面的潮流
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
PF_ES=model.addVars(N_restricted_branches,T,nameprefix='PF_ES',lb=-10000) #储能机组对断面的潮流
ES=model.addVars(N_ESs,T+1,nameprefix='ES') #储能容量剩余
Cost_ES_ch=model.addVars(N_ESs,T,nameprefix='Cost_ES_ch',lb=-1000) #储能充电成本
Cost_ES_dch=model.addVars(N_ESs,T,nameprefix='Cost_ES_dch') #储能放电成本


#---------------------------Constraints-----------------------------#
constraints=[]

#火电机组约束
for i in range(N_units):

    for t in range(T):

        #发电功率上下限约束
        model.addConstr(P_unit[i,t]<=unitdata['最大出力(MW)'][i]*U_unit[i,t],name=f'P_unit_{i}_{t}_max')
        model.addConstr(P_unit[i,t]>=unitdata['最小出力(MW)'][i]*U_unit[i,t],name=f'P_unit_{i}_{t}_min')

        #最小开机时间约束
        if unitdata['初始状态(1开机,0停机)'][i]==1: #如果初始状态为开机
            if unitdata['初始状态持续时间(h)'][i]-unitdata['最小开机时间(h)'][i]+t<0: #初始状态持续时间小于最小开机时间,则需要继续保持初始状态
                model.addConstr(U_unit[i,t]==1, name=f'V_unit_{i}_{t}_init')
        
        if t+unitdata['最小开机时间(h)'][i]<=T:
            model.addConstr(copt.quicksum([U_unit[i,k] for k in range(t,t+unitdata['最小开机时间(h)'][i])])>=unitdata['最小开机时间(h)'][i]*V_unit[i,t],name=f'V_unit_{i}_{t}_min_time')
        else:
            model.addConstr(copt.quicksum([U_unit[i,k] for k in range(t,T)])>=V_unit[i,t]*(T-t),name=f'V_unit_{i}_{t}_min_time')

        
        #最小停机时间约束
        if unitdata['初始状态(1开机,0停机)'][i]==0:    #如果初始状态为停机
            if unitdata['初始状态持续时间(h)'][i]-unitdata['最小停机时间(h)'][i]+t<0: #初始状态持续时间小于最小停机时间,则需要继续保持初始状态
                model.addConstr(U_unit[i,t]==0, name=f'W_unit_{i}_{t}_init')
        
        if t+unitdata['最小停机时间(h)'][i]<=T:
            model.addConstr(copt.quicksum([1-U_unit[i,k] for k in range(t,t+unitdata['最小停机时间(h)'][i])])>=unitdata['最小停机时间(h)'][i]*W_unit[i,t],name=f'W_unit_{i}_{t}_min_time')
        else:
            model.addConstr(copt.quicksum([1-U_unit[i,k] for k in range(t,T)])>=W_unit[i,t]*(T-t),name=f'W_unit_{i}_{t}_min_time')
        
        #启停机状态转换
        if t==0: #初始时刻的启停机状态

            model.addConstr(V_unit[i,t]>=U_unit[i,t]-unitdata['初始状态(1开机,0停机)'][i],name=f'V_unit_{i}_{t}_convert_1_init')
            model.addConstr(V_unit[i,t]<=1-unitdata['初始状态(1开机,0停机)'][i],name=f'V_unit_{i}_{t}_convert_2_init')
            model.addConstr(V_unit[i,t]<=U_unit[i,t],name=f'V_unit_{i}_{t}_convert_3_init')
            
            model.addConstr(W_unit[i,t]>=unitdata['初始状态(1开机,0停机)'][i]-U_unit[i,t],name=f'W_unit_{i}_{t}_convert_1_init')
            model.addConstr(W_unit[i,t]<=1-U_unit[i,t],name=f'W_unit_{i}_{t}_convert_2_init')
            model.addConstr(W_unit[i,t]<=unitdata['初始状态(1开机,0停机)'][i],name=f'W_unit_{i}_{t}_convert_3_init')

        
        if t>0:

            model.addConstr(V_unit[i,t]>=U_unit[i,t]-U_unit[i,t-1],name=f'V_unit_{i}_{t}_convert_1')
            model.addConstr(V_unit[i,t]<=1-U_unit[i,t-1],name=f'V_unit_{i}_{t}_convert_2')
            model.addConstr(V_unit[i,t]<=U_unit[i,t],name=f'V_unit_{i}_{t}_convert_3')
            
            model.addConstr(W_unit[i,t]>=U_unit[i,t-1]-U_unit[i,t],name=f'W_unit_{i}_{t}_convert_1')
            model.addConstr(W_unit[i,t]<=1-U_unit[i,t],name=f'W_unit_{i}_{t}_convert_2')
            model.addConstr(W_unit[i,t]<=U_unit[i,t-1],name=f'W_unit_{i}_{t}_convert_3')

    
        #爬坡率约束 （开停机动作可以不满足爬坡率约束）
        if t==0: 
            model.addConstr(P_unit[i,t]-unitdata['初始出力(MW)'][i]<=unitdata['上爬坡率(MW/h)'][i]+M*(V_unit[i,t]),name=f'P_unit_{i}_{t}_ramp_up_init')
            model.addConstr(unitdata['初始出力(MW)'][i]-P_unit[i,t]<=unitdata['下爬坡率(MW/h)'][i]+M*(W_unit[i,t]),name=f'P_unit_{i}_{t}_ramp_down_init')
        
        elif t>0:
            model.addConstr(P_unit[i,t]-P_unit[i,t-1]<=unitdata['上爬坡率(MW/h)'][i]+M*(V_unit[i,t]),name=f'P_unit_{i}_{t}_ramp_up')
            model.addConstr(P_unit[i,t-1]-P_unit[i,t]<=unitdata['下爬坡率(MW/h)'][i]+M*(W_unit[i,t]),name=f'P_unit_{i}_{t}_ramp_down')
        
        #启动成本
        model.addConstr(Cost_unit_start[i,t]==unitdata['启动成本（元）'][i]*V_unit[i,t],name=f'Cost_unit_start_{i}_{t}')
        
        #仅调试
        #model.addConstr(Cost_unit_opr[i,t]==np.mean(a_unit[i])*P_unit[i,t]+np.mean(b_unit[i])*U_unit[i,t])
        
        
        #运行成本分段线性化
        for j in range(N_unit_segs):
            
            model.addConstr(P_unit_segs[j,i,t]>=0,name=f'P_unit_segs_{j}_{i}_{t}_min')
            model.addConstr(P_unit_segs[j,i,t]<=deltaP_unit[i],name=f'P_unit_segs_{j}_{i}_{t}_max')

        #每段功率之和等于总功率
        model.addConstr(P_unit[i,t]==sum([P_unit_segs[j,i,t] for j in range(N_unit_segs)])+unitdata['最小出力(MW)'][i]*U_unit[i,t],name=f'P_unit_{i}_{t}_sum')
            
        #总成本
        model.addConstr(Cost_unit_opr[i,t]==sum(a_unit[i][j]*P_unit_segs[j,i,t] for j in range(N_unit_segs))+U_unit[i,t]*C0_unit[i],name=f'Cost_unit_opr_{i}_{t}')
        

#储能约束
for i in range(N_ESs):

    # 初始容量
    model.addConstr(ES[i, 0] == storagebasic['初始容量（MWh）'][i],name=f'ES_{i}_init')
    
    # 终止容量
    model.addConstr(ES[i, T] >= storagebasic['终止容量（MWh）'][i],name=f'ES_{i}_end')

    for t in range(T):

        #充电功率约束
        model.addConstr(P_ES_ch[i, t] == storagebasic['抽水固定功率（MW）'][i] * U_ch[i, t],name=f'P_ES_ch_{i}_{t}_fixed')
        
        #放电功率约束
        model.addConstr(P_ES_dch[i, t] >= storagebasic['最小发电功率（MW）'][i]* U_dch[i, t],name=f'P_ES_dch_{i}_{t}_min')
        model.addConstr(P_ES_dch[i, t] <=storagebasic['最大发电功率（MW）'][i]* U_dch[i, t],name=f'P_ES_dch_{i}_{t}_max')
        
        #储能容量约束
        model.addConstr(ES[i, t+1] == ES[i, t] + P_ES_ch[i, t] - P_ES_dch[i, t],name=f'ES_{i}_{t}_capacity')
        model.addConstr(ES[i, t] <= storagebasic['最大容量（MWh）'][i],name=f'ES_{i}_{t}_max')
        model.addConstr(ES[i, t] >= 0,name=f'ES_{i}_{t}_min')

        #最小抽水时间约束
        if t+storagebasic['最小抽水时段'][i]<=T:
            model.addConstr(copt.quicksum([U_ch[i, k] for k in range(t, t + storagebasic['最小抽水时段'][i])]) >= storagebasic['最小抽水时段'][i] * Z_ch[i, t],name=f'Z_ch_{i}_{t}_min_time')
        else:
            model.addConstr(copt.quicksum([U_ch[i, k] for k in range(t, T)]) >= Z_ch[i, t] * (T - t),name=f'Z_ch_{i}_{t}_min_time')

        #最小放电时间约束
        if t+storagebasic['最小发电时段'][i]<=T:
            model.addConstr(copt.quicksum([U_dch[i, k] for k in range(t, t + storagebasic['最小发电时段'][i])]) >= storagebasic['最小发电时段'][i] * Z_dch[i, t],name=f'Z_dch_{i}_{t}_min_time')
        else:
            model.addConstr(copt.quicksum([U_dch[i, k] for k in range(t, T)]) >= Z_dch[i, t] * (T - t),name=f'Z_dch_{i}_{t}_min_time')

        #最小停机时间约束
        if t+storagebasic['最小停机时段'][i]<=T:
            model.addConstr(copt.quicksum([U_ES[i, k] for k in range(t, t + storagebasic['最小停机时段'][i])]) >= storagebasic['最小停机时段'][i] * Z_ES[i, t],name=f'Z_ES_{i}_{t}_min_time')
        else:
            model.addConstr(copt.quicksum([U_ES[i, k] for k in range(t, T)]) >= Z_ES[i, t] * (T - t),name=f'Z_ES_{i}_{t}_min_time')

        #状态互斥约束
        model.addConstr(U_ch[i, t] + U_dch[i, t] + U_ES[i, t] == 1,name=f'U_{i}_{t}_mutual')

        #状态转换约束
        if t==0:
            model.addConstr(Z_dch[i, t] == U_dch[i, t]-0,name=f'Z_dch_{i}_{t}_convert_init')  #如果第一时刻选择放电，则放电indicator激活
            model.addConstr(Z_ch[i, t] == U_ch[i, t]-0,name=f'Z_ch_{i}_{t}_convert_init')
            model.addConstr(Z_ES[i, t] == 0,name=f'Z_ES_{i}_{t}_convert_init')
            
        if t > 0:
            model.addConstr(Z_ch[i, t] >= U_ch[i, t] - U_ch[i, t - 1],name=f'Z_ch_{i}_{t}_convert_1')
            model.addConstr(Z_ch[i, t] <= 1 - U_ch[i, t - 1],name=f'Z_ch_{i}_{t}_convert_2')
            model.addConstr(Z_ch[i, t] <= U_ch[i, t],name=f'Z_ch_{i}_{t}_convert_3')

            model.addConstr(Z_dch[i, t] >= U_dch[i, t] - U_dch[i, t - 1],name=f'Z_dch_{i}_{t}_convert_1')
            model.addConstr(Z_dch[i, t] <= 1-U_dch[i, t - 1],name=f'Z_dch_{i}_{t}_convert_2')
            model.addConstr(Z_dch[i, t] <= U_dch[i, t],name=f'Z_dch_{i}_{t}_convert_3')

            model.addConstr(Z_ES[i, t] >= U_ES[i, t] - U_ES[i, t - 1],name=f'Z_ES_{i}_{t}_convert_1')
            model.addConstr(Z_ES[i, t] <= 1 - U_ES[i, t - 1],name=f'Z_ES_{i}_{t}_convert_2')
            model.addConstr(Z_ES[i, t] <= U_ES[i, t],name=f'Z_ES_{i}_{t}_convert_3')

            #状态切换，充电状态与发电状态相互的切换必须经过停机状态
            model.addConstr(Z_dch[i, t] <= U_ES[i, t - 1],name=f'Z_dch_{i}_{t}_convert_4')
            model.addConstr(Z_ch[i, t] <= U_ES[i, t - 1],name=f'Z_ch_{i}_{t}_convert_4')

        #充电成本
        model.addConstr(Cost_ES_ch[i,t]==stbidprice['价格-1'][i]*U_ch[i,t],name=f'Cost_ES_ch_{i}_{t}')
        
        
        #放电成本分段线性化
        for j in range(N_ES_segs):
            model.addConstr(P_ES_dch_segs[j,i,t]>=0,name=f'P_ES_dch_segs_{j}_{i}_{t}_min')
            model.addConstr(P_ES_dch_segs[j,i,t]<=deltaP_ES[i],name=f'P_ES_dch_segs_{j}_{i}_{t}_max')

        #每段功率之和等于总功率
        model.addConstr(P_ES_dch[i,t]==copt.quicksum([P_ES_dch_segs[j,i,t] for j in range(N_ES_segs)])+storagebasic['最小发电功率（MW）'][i]*U_dch[i,t],name=f'P_ES_dch_{i}_{t}_sum')

        #总成本
        model.addConstr(Cost_ES_dch[i,t]==copt.quicksum(a_ES[i][j]*P_ES_dch_segs[j,i,t] for j in range(N_ES_segs))+U_dch[i,t]*C0_ES[i],name=f'Cost_ES_dch_{i}_{t}')

#系统约束
for t in range(T):

    #系统平衡约束
    model.addConstr(copt.quicksum(P_unit[i, t] for i in range(N_units))
                    +copt.quicksum(P_ES_dch[i, t] for i in range(N_ESs))
                    -copt.quicksum(P_ES_ch[i, t] for i in range(N_ESs))==load['系统负荷大小（MW）'][t],name=f'load_{t}')
    
    #系统备用约束
    model.addConstr(copt.quicksum(U_unit[i,t]*unitdata['最大出力(MW)'][i]-P_unit[i, t] for i in range(N_units)) >= 0.1*load['系统负荷大小（MW）'][t],name=f'system_reserve_{t}')
    
    
    #断面约束
    for j in range(N_restricted_branches):

        #找到对应的断面在gen_senses中的位置
        branch_idx=gen_senses[gen_senses['支路中文名']==restricted_branches[j]].index[0]
    
        model.addConstr(PF_unit[j,t]==copt.quicksum(P_unit[i,t]*gen_senses[f'{i+1}对所列支路潮流的灵敏度值'][branch_idx] for i in range(N_units)),name=f'PF_unit_{j}_{t}')

        #储能机组对断面的潮流
        model.addConstr(PF_ES[j,t]==copt.quicksum((P_ES_dch[i,t]-P_ES_ch[i,t])*gen_senses[f'{len(unitdata)}对所列支路潮流的灵敏度值'][branch_idx] for i in range(N_ESs)),name=f'PF_ES_{j}_{t}')

        #断面潮流约束
        model.addConstr(PF_unit[j,t]+PF_ES[j,t]-PF_load[j,t]<=section['断面限额'][j],name=f'PF_{j}_{t}_max1')
        model.addConstr(PF_unit[j,t]+PF_ES[j,t]-PF_load[j,t]>=-section['断面限额'][j],name=f'PF_{j}_{t}_max2')

#---------------------------------Objective---------------------------------#
#目标函数=火电机组的启动成本+火电机组的运行成本+储能机组的运行成本
                  
model.setObjective(copt.quicksum(Cost_unit_start)+copt.quicksum(Cost_unit_opr)+copt.quicksum(Cost_ES_ch)+copt.quicksum(Cost_ES_dch), 
                   sense=copt.COPT.MINIMIZE)

#---------------------------------Solve---------------------------------#
model.setParam("Logging", 1)
model.setParam("RelGap", 0.0003)
#model.setParam("GPUMode",1)
model.setParam("DivingHeurLevel",2)
#model.setParam("StrongBranching",2)
#model.setParam("MipStartMode",2)
model.setParam("TimeLimit",3600)

model.solve()
if model.status == copt.COPT.INFEASIBLE:
  # Compute IIS
  model.computeIIS()
  model.writeIIS('iis_ex1.iis')


#整理变量
P_unit_val=np.array([[P_unit[i,t].value for t in range(T)] for i in range(N_units)])
U_unit_val=np.array([[int(np.round(U_unit[i,t].value)) for t in range(T)] for i in range(N_units)])
U_ch_val=np.array([[int(np.round(U_ch[i,t].value)) for t in range(T)] for i in range(N_ESs)])
U_dch_val=np.array([[int(np.round(U_dch[i,t].value)) for t in range(T)] for i in range(N_ESs)])
U_ES_val=np.array([[int(np.round(U_ES[i,t].value)) for t in range(T)] for i in range(N_ESs)])
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
Cost_ES_ch_val,Cost_ES_dch_val,Cost_unit_start_val,Cost_unit_opr_val=calculateCosts(P_ES_ch_val,P_ES_dch_val,U_ch_val,U_dch_val,P_unit_val,U_unit_val)
print('校验火电机组启动成本:',Cost_unit_start_val)
print('校验火电机组运行成本:',Cost_unit_opr_val)
print('校验储能机组充电成本:',Cost_ES_ch_val)
print('校验储能机组放电成本:',Cost_ES_dch_val)
print('校验总成本:',Cost_unit_start_val+Cost_unit_opr_val+Cost_ES_ch_val+Cost_ES_dch_val)
print('---------------------------------')


#校验外部最优解对应的成本

#如果路径存在：
if os.path.exists(f'data/instances/{instance_num}/solution.sol'):

    Vars=utils.readSols(f'data/instances/{instance_num}/solution.sol')
    utils.Sols2Excel(**Vars,instance_num=instance_num,is_opt=True)
    Vars.pop('U_ES')
    Cost_ES_ch_val,Cost_ES_dch_val,Cost_unit_start_val,Cost_unit_opr_val=calculateCosts(**Vars)
    print('外部最优解校验火电机组启动成本:',Cost_unit_start_val)
    print('外部最优解校验火电机组运行成本:',Cost_unit_opr_val)
    print('外部最优解校验储能机组充电成本:',Cost_ES_ch_val)
    print('外部最优解校验储能机组放电成本:',Cost_ES_dch_val)
    print('外部最优解校验总成本:',Cost_unit_start_val+Cost_unit_opr_val+Cost_ES_ch_val+Cost_ES_dch_val)

#写入excel
utils.Sols2Excel(U_unit_val,P_unit_val,U_ch_val,U_dch_val,U_ES_val,P_ES_ch_val,P_ES_dch_val,instance_num=instance_num,is_opt=False)

#写入solution.sol
utils.writeSols(model,U_unit_val,P_unit_val,U_ch_val,U_dch_val,U_ES_val,P_ES_ch_val,P_ES_dch_val,instance_num=instance_num)



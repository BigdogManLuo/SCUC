import coptpy as copt
from params import *

def defineModel():

    global N_units,T,N_unit_segs,N_restricted_branches,N_ESs,N_ES_segs,M,unitdata,deltaP_unit,a_unit,C0_unit,a_ES,deltaP_ES,C0_ES,restricted_branches,PF_load,load,section,gen_senses,stbidprice,stbidcapactiy,storagebasic

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

    return model

def solveModel(model,**kwargs):

    #---------------------------------Solve---------------------------------#
    model.setParam("Logging", 1)
    model.setParam("RelGap", kwargs['RelGap'])
    model.setParam("TimeLimit", kwargs['TimeLimit'])
    model.solve()

    return model


if __name__ == '__main__':
    model=defineModel()
    model=solveModel(model,RelGap=1e-4,TimeLimit=600)
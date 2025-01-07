import utils
import numpy as np

#输入求解的样例编号
instance_num=60 

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

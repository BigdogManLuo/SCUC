*SENSE:Minimize
NAME          Unit_Commitment
ROWS
 N  OBJ
 E  Demand_0
 E  Demand_1
 G  Min_Power_0_Gen2
 L  Max_Power_0_Gen2
 G  Min_Power_0_Gen3
 L  Max_Power_0_Gen3
 G  Min_Power_1_Gen2
 L  Max_Power_1_Gen2
 G  Min_Power_1_Gen3
 L  Max_Power_1_Gen3
 G  Startup_1_Gen1
 G  Startup_1_Gen2
 G  Startup_1_Gen3
 L  Commit_0_Gen1
 L  Commit_0_Gen2
 L  Commit_0_Gen3
 L  Commit_1_Gen1
 L  Commit_1_Gen2
 L  Commit_1_Gen3
COLUMNS
    p_(0,_'Gen1')  Demand_0   1.000000000000e+00
    p_(0,_'Gen1')  OBJ        1.000000000000e+01
    p_(0,_'Gen2')  Demand_0   1.000000000000e+00
    p_(0,_'Gen2')  Min_Power_0_Gen2   1.000000000000e+00
    p_(0,_'Gen2')  Max_Power_0_Gen2   1.000000000000e+00
    p_(0,_'Gen2')  OBJ        1.200000000000e+01
    p_(0,_'Gen3')  Demand_0   1.000000000000e+00
    p_(0,_'Gen3')  Min_Power_0_Gen3   1.000000000000e+00
    p_(0,_'Gen3')  Max_Power_0_Gen3   1.000000000000e+00
    p_(0,_'Gen3')  OBJ        1.500000000000e+01
    p_(1,_'Gen1')  Demand_1   1.000000000000e+00
    p_(1,_'Gen1')  OBJ        1.000000000000e+01
    p_(1,_'Gen2')  Demand_1   1.000000000000e+00
    p_(1,_'Gen2')  Min_Power_1_Gen2   1.000000000000e+00
    p_(1,_'Gen2')  Max_Power_1_Gen2   1.000000000000e+00
    p_(1,_'Gen2')  OBJ        1.200000000000e+01
    p_(1,_'Gen3')  Demand_1   1.000000000000e+00
    p_(1,_'Gen3')  Min_Power_1_Gen3   1.000000000000e+00
    p_(1,_'Gen3')  Max_Power_1_Gen3   1.000000000000e+00
    p_(1,_'Gen3')  OBJ        1.500000000000e+01
    MARK      'MARKER'                 'INTORG'
    u_(0,_'Gen1')  Startup_1_Gen1  -1.000000000000e+00
    u_(0,_'Gen1')  Commit_0_Gen1   1.000000000000e+00
    u_(0,_'Gen1')  OBJ        3.000000000000e+01
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    u_(0,_'Gen2')  Min_Power_0_Gen2  -3.000000000000e+01
    u_(0,_'Gen2')  Max_Power_0_Gen2  -1.500000000000e+02
    u_(0,_'Gen2')  Startup_1_Gen2  -1.000000000000e+00
    u_(0,_'Gen2')  Commit_0_Gen2   1.000000000000e+00
    u_(0,_'Gen2')  OBJ        2.000000000000e+01
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    u_(0,_'Gen3')  Min_Power_0_Gen3  -4.000000000000e+01
    u_(0,_'Gen3')  Max_Power_0_Gen3  -1.200000000000e+02
    u_(0,_'Gen3')  Startup_1_Gen3  -1.000000000000e+00
    u_(0,_'Gen3')  Commit_0_Gen3   1.000000000000e+00
    u_(0,_'Gen3')  OBJ        4.000000000000e+01
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    u_(1,_'Gen1')  Startup_1_Gen1   1.000000000000e+00
    u_(1,_'Gen1')  Commit_1_Gen1   1.000000000000e+00
    u_(1,_'Gen1')  OBJ        3.000000000000e+01
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    u_(1,_'Gen2')  Min_Power_1_Gen2  -3.000000000000e+01
    u_(1,_'Gen2')  Max_Power_1_Gen2  -1.500000000000e+02
    u_(1,_'Gen2')  Startup_1_Gen2   1.000000000000e+00
    u_(1,_'Gen2')  Commit_1_Gen2   1.000000000000e+00
    u_(1,_'Gen2')  OBJ        2.000000000000e+01
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    u_(1,_'Gen3')  Min_Power_1_Gen3  -4.000000000000e+01
    u_(1,_'Gen3')  Max_Power_1_Gen3  -1.200000000000e+02
    u_(1,_'Gen3')  Startup_1_Gen3   1.000000000000e+00
    u_(1,_'Gen3')  Commit_1_Gen3   1.000000000000e+00
    u_(1,_'Gen3')  OBJ        4.000000000000e+01
    MARK      'MARKER'                 'INTEND'
RHS
    RHS       Demand_0   1.500000000000e+02
    RHS       Demand_1   1.800000000000e+02
    RHS       Min_Power_0_Gen2   0.000000000000e+00
    RHS       Max_Power_0_Gen2   0.000000000000e+00
    RHS       Min_Power_0_Gen3   0.000000000000e+00
    RHS       Max_Power_0_Gen3   0.000000000000e+00
    RHS       Min_Power_1_Gen2   0.000000000000e+00
    RHS       Max_Power_1_Gen2   0.000000000000e+00
    RHS       Min_Power_1_Gen3   0.000000000000e+00
    RHS       Max_Power_1_Gen3   0.000000000000e+00
    RHS       Startup_1_Gen1   0.000000000000e+00
    RHS       Startup_1_Gen2   0.000000000000e+00
    RHS       Startup_1_Gen3   0.000000000000e+00
    RHS       Commit_0_Gen1   1.000000000000e+00
    RHS       Commit_0_Gen2   1.000000000000e+00
    RHS       Commit_0_Gen3   1.000000000000e+00
    RHS       Commit_1_Gen1   1.000000000000e+00
    RHS       Commit_1_Gen2   1.000000000000e+00
    RHS       Commit_1_Gen3   1.000000000000e+00
BOUNDS
 BV BND       u_(0,_'Gen1')
 BV BND       u_(0,_'Gen2')
 BV BND       u_(0,_'Gen3')
 BV BND       u_(1,_'Gen1')
 BV BND       u_(1,_'Gen2')
 BV BND       u_(1,_'Gen3')
ENDATA

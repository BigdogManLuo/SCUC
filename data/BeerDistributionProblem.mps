*SENSE:Minimize
NAME          Beer_Distribution_Problem
ROWS
 N  Sum_of_Transporting_Costs
 L  Sum_of_Products_out_of_Warehouse_A
 L  Sum_of_Products_out_of_Warehouse_B
 L  Sum_of_Products_out_of_Warehouse_C
 G  Sum_of_Products_into_Bar1
 G  Sum_of_Products_into_Bar2
 G  Sum_of_Products_into_Bar3
 G  Sum_of_Products_into_Bar4
 G  Sum_of_Products_into_Bar5
COLUMNS
    MARK      'MARKER'                 'INTORG'
    Route_A_1  Sum_of_Products_out_of_Warehouse_A   1.000000000000e+00
    Route_A_1  Sum_of_Products_into_Bar1   1.000000000000e+00
    Route_A_1  Sum_of_Transporting_Costs   2.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_A_2  Sum_of_Products_out_of_Warehouse_A   1.000000000000e+00
    Route_A_2  Sum_of_Products_into_Bar2   1.000000000000e+00
    Route_A_2  Sum_of_Transporting_Costs   4.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_A_3  Sum_of_Products_out_of_Warehouse_A   1.000000000000e+00
    Route_A_3  Sum_of_Products_into_Bar3   1.000000000000e+00
    Route_A_3  Sum_of_Transporting_Costs   5.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_A_4  Sum_of_Products_out_of_Warehouse_A   1.000000000000e+00
    Route_A_4  Sum_of_Products_into_Bar4   1.000000000000e+00
    Route_A_4  Sum_of_Transporting_Costs   2.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_A_5  Sum_of_Products_out_of_Warehouse_A   1.000000000000e+00
    Route_A_5  Sum_of_Products_into_Bar5   1.000000000000e+00
    Route_A_5  Sum_of_Transporting_Costs   1.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_B_1  Sum_of_Products_out_of_Warehouse_B   1.000000000000e+00
    Route_B_1  Sum_of_Products_into_Bar1   1.000000000000e+00
    Route_B_1  Sum_of_Transporting_Costs   3.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_B_2  Sum_of_Products_out_of_Warehouse_B   1.000000000000e+00
    Route_B_2  Sum_of_Products_into_Bar2   1.000000000000e+00
    Route_B_2  Sum_of_Transporting_Costs   1.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_B_3  Sum_of_Products_out_of_Warehouse_B   1.000000000000e+00
    Route_B_3  Sum_of_Products_into_Bar3   1.000000000000e+00
    Route_B_3  Sum_of_Transporting_Costs   3.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_B_4  Sum_of_Products_out_of_Warehouse_B   1.000000000000e+00
    Route_B_4  Sum_of_Products_into_Bar4   1.000000000000e+00
    Route_B_4  Sum_of_Transporting_Costs   2.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_B_5  Sum_of_Products_out_of_Warehouse_B   1.000000000000e+00
    Route_B_5  Sum_of_Products_into_Bar5   1.000000000000e+00
    Route_B_5  Sum_of_Transporting_Costs   3.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_C_1  Sum_of_Products_out_of_Warehouse_C   1.000000000000e+00
    Route_C_1  Sum_of_Products_into_Bar1   1.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_C_2  Sum_of_Products_out_of_Warehouse_C   1.000000000000e+00
    Route_C_2  Sum_of_Products_into_Bar2   1.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_C_3  Sum_of_Products_out_of_Warehouse_C   1.000000000000e+00
    Route_C_3  Sum_of_Products_into_Bar3   1.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_C_4  Sum_of_Products_out_of_Warehouse_C   1.000000000000e+00
    Route_C_4  Sum_of_Products_into_Bar4   1.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    MARK      'MARKER'                 'INTORG'
    Route_C_5  Sum_of_Products_out_of_Warehouse_C   1.000000000000e+00
    Route_C_5  Sum_of_Products_into_Bar5   1.000000000000e+00
    MARK      'MARKER'                 'INTEND'
RHS
    RHS       Sum_of_Products_out_of_Warehouse_A   1.000000000000e+03
    RHS       Sum_of_Products_out_of_Warehouse_B   4.000000000000e+03
    RHS       Sum_of_Products_out_of_Warehouse_C   1.000000000000e+02
    RHS       Sum_of_Products_into_Bar1   5.000000000000e+02
    RHS       Sum_of_Products_into_Bar2   9.000000000000e+02
    RHS       Sum_of_Products_into_Bar3   1.800000000000e+03
    RHS       Sum_of_Products_into_Bar4   2.000000000000e+02
    RHS       Sum_of_Products_into_Bar5   7.000000000000e+02
BOUNDS
 LO BND       Route_A_1   0.000000000000e+00
 LO BND       Route_A_2   0.000000000000e+00
 LO BND       Route_A_3   0.000000000000e+00
 LO BND       Route_A_4   0.000000000000e+00
 LO BND       Route_A_5   0.000000000000e+00
 LO BND       Route_B_1   0.000000000000e+00
 LO BND       Route_B_2   0.000000000000e+00
 LO BND       Route_B_3   0.000000000000e+00
 LO BND       Route_B_4   0.000000000000e+00
 LO BND       Route_B_5   0.000000000000e+00
 LO BND       Route_C_1   0.000000000000e+00
 LO BND       Route_C_2   0.000000000000e+00
 LO BND       Route_C_3   0.000000000000e+00
 LO BND       Route_C_4   0.000000000000e+00
 LO BND       Route_C_5   0.000000000000e+00
ENDATA

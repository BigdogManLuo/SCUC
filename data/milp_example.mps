*SENSE:Maximize
NAME          Maximize_Z
ROWS
 N  Z
 L  _C1
 G  _C2
 G  _C3
COLUMNS
    MARK      'MARKER'                 'INTORG'
    x         _C1        1.000000000000e+00
    x         _C2        1.000000000000e+00
    x         Z          3.000000000000e+00
    MARK      'MARKER'                 'INTEND'
    y         _C1        1.000000000000e+00
    y         _C3        1.000000000000e+00
    y         Z          2.000000000000e+00
RHS
    RHS       _C1        5.000000000000e+00
    RHS       _C2        1.000000000000e+00
    RHS       _C3        2.000000000000e+00
BOUNDS
 LO BND       x          1.000000000000e+00
 LO BND       y          2.000000000000e+00
ENDATA

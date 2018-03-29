import generator.terminal as t
import generator.rule     as r
import generator.compiler as c

from CNC.language import Registers  as reg
from CNC.language import Commands as cmd
import CNC.language as CNC

import expression2          as expr
import grammars.heidenhain  as hh

from enum import Enum, unique
from copy import deepcopy

@unique
class GOTOtokensCartesian(Enum):
  linear    = "L "
  circular  = "C " # whitespace does not match CC

@unique
class GOTOtokensPolar(Enum):
  linear    = "LP"
  circular  = "CP"

cmdLookup = t.make_lookup({
  GOTOtokensCartesian.linear    : [ CNC.Motion.LINEAR,    reg.MOTIONMODE, cmd.SETREG, cmd.MOVE ],
  GOTOtokensCartesian.circular  : [ CNC.Motion.CIRCULAR,  reg.MOTIONMODE, cmd.SETREG, cmd.MOVE ],
  GOTOtokensPolar.linear        : [ CNC.Motion.LINEAR,    reg.MOTIONMODE, cmd.SETREG, cmd.MOVE ],
  GOTOtokensPolar.circular      : [ CNC.Motion.CIRCULAR,  reg.MOTIONMODE, cmd.SETREG, cmd.MOVE ]
})

  
@unique
class ToolCallTokens(Enum):
  DR = 'DR\\s*='
  DL = 'DL\\s*='
  S  = 'S'

@unique
class CartCoordinateTokens(Enum):
  X = "(I)?(X)"
  Y = "(I)?(Y)"
  Z = "(I)?(Z)"
  A = "(I)?(A)"
  B = "(I)?(B)"
  C = "(I)?(C)"
  
@unique
class PolarCoordinateTokens(Enum):
  PA = "(I)?(P)(A)"
  PR = "(I)?(P)(R)"

coordmap = { 'X' : reg.X, 'Y' : reg.Y, 'Z' : reg.Z, 'A' : reg.ANG, 'R' : reg.RAD }
maskmap = { reg.X : reg.XINC, reg.Y : reg.YINC, reg.Z : reg.ZINC, reg.ANG : reg.ANGINC, reg.RAD : reg.RADINC }
  
def handleCoord( token ):
  token = token[0]
  symbol = token.groups[len(token.groups)-1]
  polar = False
  incremental = False
  if len( token.groups ) == 3:
    incremental = token.groups[0] is 'I'
    polar = token.groups[1] is 'P'
    symbol = token.groups[2]
  elif len( token.groups ) == 2:
    incremental = token.groups[0] is 'I'
    symbol = token.groups[1]
  symbol = coordmap[symbol]
  inc = maskmap[symbol]
  return [ symbol, cmd.SETREG, int(incremental), inc, cmd.SETREG ]

@unique
class Compensation(Enum):
  R0 = 'R0'
  RR = 'RR'
  RL = 'RL'  
  
compensationLookup = t.make_lookup( { 
  Compensation.R0 : [ CNC.Compensation.NONE, reg.COMPENSATION, cmd.SETREG ]
, Compensation.RL : [ CNC.Compensation.LEFT, reg.COMPENSATION, cmd.SETREG ]
, Compensation.RR : [ CNC.Compensation.RIGHT, reg.COMPENSATION, cmd.SETREG ]
} )

@unique
class Direction( Enum ):
  CW = 'DR[-]'
  CCW = 'DR[+]'

directionLookup = t.make_lookup( { 
  Direction.CW  : [ CNC.Direction.CW,   reg.DIRECTION, cmd.SETREG ]
, Direction.CCW : [ CNC.Direction.CCW,  reg.DIRECTION, cmd.SETREG ]
} )

terminals = t.make({
  'coordCartesian'    : t.make( CartCoordinateTokens ) >> handleCoord,
  'coordPolar'        : t.make( PolarCoordinateTokens ) >> handleCoord,
  'F'                 : t.make('F').ignore( [ reg.FEED, cmd.SETREG ] ),
  'MAX'               : t.make('MAX').ignore( [ -1 ] ),
  'compensation'      : compensationLookup(Compensation),
  'direction'         : directionLookup( Direction ),
  'L/C'               : cmdLookup(GOTOtokensCartesian),
  'LP/CP'             : cmdLookup(GOTOtokensPolar),
  'CC'                : t.make('CC').ignore(),
  'M'                 : 'M',
  'begin_pgm'         : 'BEGIN PGM (.+) (MM|INCH)',
  'end_pgm'           : 'END PGM (.+)',
  'comment'           : '[;][ ]*(.*)',
  'block form start'  : 'BLK FORM 0\\.1 (X|Y|Z)',
  'block form end'    : 'BLK FORM 0\\.2',
  'fn_f'              : 'FN[ ]*(\\d+)\\:',
  'tool call'         : t.make('TOOL CALL') >> t.get(t.Task.match),
  'tool axis'         : t.make('(X|Y|Z)') >> t.get(t.Task.match),
  'tool options'      : t.make(ToolCallTokens) >> t.get(t.Task.match) ,
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
})

Parse = t.StrParser( hh.heidenhain, c.Reordering( terminals ) )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  for i in range(n):
    q = Parse( 'L X+50 Y-30 Z+150 R0 FMAX' )
  print( time.time() - start )
  print(q[0])
  print(q[1])
  
bench()
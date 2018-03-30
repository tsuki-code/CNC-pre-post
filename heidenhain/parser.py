import generator.terminal as t
import generator.rule     as r
import generator.compiler as c

import heidenhain.commands as commands
from heidenhain.commands import Registers     as reg
from heidenhain.commands import Commands      as cmd
from heidenhain.commands import Motion        as mot
from heidenhain.commands import Compensation  as comp
from heidenhain.commands import Direction     as dir

from expression.commands import Arithmetic    as art

import expression.parser    as expr
import heidenhain.grammar   as hh

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
  GOTOtokensCartesian.linear    : [ mot.LINEAR,    reg.MOTIONMODE, art.SETREG, cmd.MOVE ],
  GOTOtokensCartesian.circular  : [ mot.CIRCULAR,  reg.MOTIONMODE, art.SETREG, cmd.MOVE ],
  GOTOtokensPolar.linear        : [ mot.LINEAR,    reg.MOTIONMODE, art.SETREG, cmd.MOVE ],
  GOTOtokensPolar.circular      : [ mot.CIRCULAR,  reg.MOTIONMODE, art.SETREG, cmd.MOVE ]
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

coordmap = { 
  'X' : reg.X, 'Y' : reg.Y, 'Z' : reg.Z, 
  'A' : reg.A, 'B' : reg.B, 'C' : reg.C, 
  'R' : reg.RAD 
}
  
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
  if symbol is reg.A and polar: 
    symbol = reg.ANG
  inc = commands.incmap[symbol]
  return [ symbol, art.SETREG, int(incremental), inc, art.SETREG ]

@unique
class Compensation(Enum):
  R0 = 'R0'
  RR = 'RR'
  RL = 'RL'  
  
compensationLookup = t.make_lookup( { 
  Compensation.R0 : [ comp.NONE,  reg.COMPENSATION, art.SETREG ]
, Compensation.RL : [ comp.LEFT,  reg.COMPENSATION, art.SETREG ]
, Compensation.RR : [ comp.RIGHT, reg.COMPENSATION, art.SETREG ]
} )

@unique
class Direction( Enum ):
  CW = 'DR[-]'
  CCW = 'DR[+]'

directionLookup = t.make_lookup( { 
  Direction.CW  : [ dir.CW,   reg.DIRECTION, art.SETREG ]
, Direction.CCW : [ dir.CCW,  reg.DIRECTION, art.SETREG ]
} )

terminals = t.make({
  'coordCartesian'    : t.make( CartCoordinateTokens ) >> handleCoord,
  'coordPolar'        : t.make( PolarCoordinateTokens ) >> handleCoord,
  'F'                 : t.make('F').ignore( [ reg.FEED, art.SETREG ] ),
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
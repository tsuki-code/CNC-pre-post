import generator.terminal as t
import generator.rule     as r
import generator.compiler as c

import languages.heidenhain.commands as commands

from languages.heidenhain.commands import Commands      as cmd
from languages.heidenhain.commands import Registers     as reg
from languages.heidenhain.commands import Cartesian     as cart
from languages.heidenhain.commands import Polar         as pol
from languages.heidenhain.commands import Angular       as ang
from languages.heidenhain.commands import Center        as cen
from languages.heidenhain.commands import Motion        as mot
from languages.heidenhain.commands import Compensation  as comp
from languages.heidenhain.commands import Direction     as dir
from languages.heidenhain.commands import Coolant       as cool
from languages.heidenhain.commands import Spindle       as spin

import languages.expression.commands as art

import languages.expression.parser    as expr
import languages.heidenhain.grammar   as hh

from enum import Enum, unique
from copy import deepcopy

GOTOcartesian = t.Switch({ 
  'L '  : t.Return( mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ),
  'C '  : t.Return( mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT )
})

GOTOpolar = t.Switch({ 
  'LP'  : t.Return( mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ),
  'CP'  : t.Return( mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT )
})

toolCallOptions = t.Switch({
  'DR\\s*[=]?'  : t.Return( reg.TOOLDR,    cmd.SET ),
  'DL\\s*[=]?'  : t.Return( reg.TOOLDL,    cmd.SET ),
  'S'           : t.Return( reg.SPINSPEED, cmd.SET )
})

def handleCoord( map ):
  def _handleCoord( token ):
    symbol = map[ token.groups()[1] ]
    if token.groups()[0] is 'I':
      symbol = commands.incmap[symbol]
    return [ symbol, cmd.SET ]
  return _handleCoord
  
coordmap = { 
  'X' : cart.X, 'Y' : cart.Y, 'Z' : cart.Z, 
  'A' : ang.A, 'B' : ang.B, 'C' : ang.C, 
  'PA' : pol.ANG, 'PR' : pol.RAD 
}

cartesianCoord = t.Switch({
  "(I)?(X)" : handleCoord(coordmap),
  "(I)?(Y)" : handleCoord(coordmap),
  "(I)?(Z)" : handleCoord(coordmap),
  "(I)?(A)" : handleCoord(coordmap),
  "(I)?(B)" : handleCoord(coordmap),
  "(I)?(C)" : handleCoord(coordmap)
})

polarCoord = t.Switch({
  '(I)?(PA)' : handleCoord(coordmap),
  '(I)?(PR)' : handleCoord(coordmap)
})

CCcoordmap = { 
 'X' : cen.X, 'Y' : cen.Y, 'Z' : cen.Z
}

CCcoord = t.Switch({
  "(I)?(X)" : handleCoord(CCcoordmap),
  "(I)?(Y)" : handleCoord(CCcoordmap),
  "(I)?(Z)" : handleCoord(CCcoordmap)
})
  
compensation = t.Switch( { 
  'R0' : t.Return( comp.NONE,  reg.COMPENSATION, cmd.SET ),
  'RL' : t.Return( comp.LEFT,  reg.COMPENSATION, cmd.SET ),
  'RR' : t.Return( comp.RIGHT, reg.COMPENSATION, cmd.SET )
} )

direction = t.Switch( { 
  'DR[-]' : t.Return( dir.CW,   reg.DIRECTION, cmd.SET ),
  'DR[+]' : t.Return( dir.CCW,  reg.DIRECTION, cmd.SET )
} )

def handleAux( result ):
  aux = int(result[0].groups[0])
  command = { 
    0  : [ cmd.STOP ], 
    1  : [ cmd.OPTSTOP ], 
    3  : [ spin.CW,  reg.SPINDIR, cmd.SET ],
    4  : [ spin.CCW, reg.SPINDIR, cmd.SET ],
    5  : [ spin.OFF, reg.SPINDIR, cmd.SET ],
    6  : [ cmd.TOOLCHANGE ], 
    8  : [ cool.FLOOD, reg.COOLANT, cmd.SET ],
    9  : [ cool.OFF,   reg.COOLANT, cmd.SET ],
    30 : [ cmd.END ],
    91 : [ reg.WCS, cmd.TMP, 0, reg.WCS, cmd.SET ]
  }
  try:
    return command[aux]
  except KeyError:
    raise RuntimeError('Unknown auxillary function M'+str(aux) )
    
auxilary = t.Switch({ 'M(\\d+)' : handleAux })  


terminals = {
  'XYZABC'            : cartesianCoord,
  'PAPR'              : polarCoord,
  'CCXYZ'             : CCcoord,
  'lineno'            : t.Wrapper( expr.number ,(lambda x : [ x[0], reg.LINENO, cmd.SET ]) ),
  'F'                 : t.Switch({ 'F' : t.Return( reg.FEED, cmd.SET ) }),
  'MAX'               : t.Switch({ 'MAX' : t.Return( -1 ) }),
  'compensation'      : compensation,
  'direction'         : direction,
  'L/C'               : GOTOcartesian,
  'LP/CP'             : GOTOpolar,
  'MOVE'              : t.Return( cmd.INVARIANT ),
  'UPDATE'            : t.Return( cmd.INVARIANT ),
  'CC'                : t.Switch({ 'CC' : t.Return( cmd.INVARIANT ) }),
  'auxilary'          : auxilary,
  'begin_pgm'         : t.Switch({ 'BEGIN PGM (.+) (MM|INCH)' : t.Return() }),
  'end_pgm'           : t.Switch({ 'END PGM (.+)' : t.Return() }),
  'comment'           : t.Switch({ '[;][ ]*(.*)' : t.Return() }),
  'block form start'  : t.Switch({ 'BLK FORM 0\\.1 (X|Y|Z)'  : t.Return(cmd.DISCARD) }),
  'block form end'    : t.Switch({ 'BLK FORM 0\\.2'  : t.Return(cmd.DISCARD) }),
  'fn_f'              : t.Switch({ 'FN 0\\:'  : t.Return(cmd.INVARIANT) }),
  'tool call'         : t.Switch({ 'TOOL CALL' : t.Return( reg.TOOLNO, cmd.SET, cmd.INVARIANT, cmd.TOOLCHANGE )}),
  'tool axis'         : t.Switch({ '(X|Y|Z)' : t.Return() }),
  'tool options'      : toolCallOptions,
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
}

# Parse = t.StrParser( hh.heidenhain, c.Reordering( terminals ) )
Parse = hh.heidenhain.compile( c.Reordering( terminals ) )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  for i in range(n):
    q = Parse( 'L X+50 Y-30 Z+150 R0 FMAX' )
  print( time.time() - start )
  print(q[0])
  print(q[1])
  
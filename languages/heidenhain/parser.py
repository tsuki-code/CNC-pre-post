import re

from generator.terminal import *
from generator import State
import generator.rule       as r
import generator.compiler   as c

import languages.heidenhain.commands as cmd

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

p = re.compile

GOTOcartesian = Lookup({ 
  p('L ')  : ( cmd.setval(reg.MOTIONMODE, mot.LINEAR), cmd.invariant ),
  p('C ')  : ( cmd.setval(reg.MOTIONMODE, mot.CIRCULAR), cmd.invariant )
}.items())

GOTOpolar = Lookup({ 
  p('LP')  : ( cmd.setval(reg.MOTIONMODE, mot.LINEAR), cmd.invariant ),
  p('CP')  : ( cmd.setval(reg.MOTIONMODE, mot.CIRCULAR), cmd.invariant )
}.items())

toolCallOptions = Lookup({
  p('DR\\s*[=]?')  : ( cmd.Set( reg.TOOLDR ), ),
  p('DL\\s*[=]?')  : ( cmd.Set( reg.TOOLDL ), ),
  p('S')           : ( cmd.Set( reg.SPINSPEED ), )
}.items())

def handleCoord( map ):
  def _handleCoord( match ):
    symbol = map[ match.groups()[1] ]
    if match.groups()[0] is 'I':
      symbol = commands.incmap[symbol]
    return ( cmd.Set(symbol), )
  return _handleCoord
  
coordmap = { 
  'X' : cart.X, 'Y' : cart.Y, 'Z' : cart.Z, 
  'A' : ang.A, 'B' : ang.B, 'C' : ang.C, 
  'PA' : pol.ANG, 'PR' : pol.RAD 
}

cartesianCoord = Switch({
  p(pattern) : handleCoord(coordmap) for pattern in
  [ "(I)?(X)", "(I)?(Y)", "(I)?(Z)", 
    "(I)?(A)", "(I)?(B)", "(I)?(C)"]
}.items())

polarCoord = Switch({
  p('(I)?(PA)') : handleCoord(coordmap),
  p('(I)?(PR)') : handleCoord(coordmap)
}.items())

CCcoordmap = { 'X' : cen.X, 'Y' : cen.Y, 'Z' : cen.Z }

CCcoord = Switch({
  p(pattern) : handleCoord(CCcoordmap) for pattern in
  [ "(I)?(X)", "(I)?(Y)", "(I)?(Z)" ]
}.items())
  
compensation = Lookup( { 
  p('R0') : ( cmd.setval(reg.COMPENSATION, comp.NONE), ),
  p('RL') : ( cmd.setval(reg.COMPENSATION, comp.LEFT), ),
  p('RR') : ( cmd.setval(reg.COMPENSATION, comp.RIGHT), )
}.items())

direction = Lookup( { 
  p('DR[-]') : ( cmd.setval(reg.DIRECTION, dir.CW), ),
  p('DR[+]') : ( cmd.setval(reg.DIRECTION, dir.CCW), )
}.items())

def handleAux( match ):
  aux = int(match.groups()[0])
  command = { 
    0  : ( cmd.stop, ), 
    1  : ( cmd.optionalStop, ), 
    3  : ( cmd.setval(reg.SPINDIR, spin.CW), ),
    4  : ( cmd.setval(reg.SPINDIR, spin.CCW), ),
    5  : ( cmd.setval(reg.SPINDIR, spin.OFF), ),
    6  : ( cmd.toolchange, ), 
    8  : ( cmd.setval(reg.COOLANT, cool.FLOOD), ),
    9  : ( cmd.setval(reg.COOLANT, cool.OFF), ),
    30 : ( cmd.end, ),
    91 : ( cmd.Temporary(reg.WCS), cmd.setval(reg.WCS, 0) )
  }
  try:
    return command[aux]
  except KeyError:
    raise RuntimeError('Unknown auxillary function M'+str(aux) )

terminals = {
  'XYZABC'            : cartesianCoord,
  'PAPR'              : polarCoord,
  'CCXYZ'             : CCcoord,
  'lineno'            : Wrapper( expr.number , lambda x : ( cmd.setval(reg.LINENO, x[0]), ) ),
  'F'                 : Return( cmd.Set(reg.FEED) ).If(p('F')),
  'MAX'               : Return( Push(-1) ).If(p('MAX')),
  'compensation'      : compensation,
  'direction'         : direction,
  'L/C'               : GOTOcartesian,
  'LP/CP'             : GOTOpolar,
  'MOVE'              : Return( cmd.invariant ),
  'UPDATE'            : Return( cmd.invariant ),
  'CC'                : Return( cmd.invariant ).If(p('CC')),
  'auxilary'          : If(p('M(\\d+)'), handleAux),
  'begin_pgm'         : Return().If(p('BEGIN PGM (.+) (MM|INCH)')),
  'end_pgm'           : Return().If(p('END PGM (.+)')),
  'comment'           : Return().If(p('[;][ ]*(.*)')),
  'block form start'  : Return(cmd.discard).If(p('BLK FORM 0\\.1 (X|Y|Z)')),
  'block form end'    : Return(cmd.discard).If(p('BLK FORM 0\\.2')),
  'fn_f'              : Return(cmd.invariant).If(p('FN 0\\:')),
  'tool call'         : Return(cmd.Set(reg.TOOLNO), cmd.invariant, cmd.toolchange ).If(p('TOOL CALL')),
  'tool axis'         : Return().If(p('(X|Y|Z)')),
  'tool options'      : toolCallOptions,
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
}

terminals = pushTerminals( terminals )

Parse = hh.heidenhain.compile( c.Reordering( terminals ) )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  r = None
  for i in range(n):
    q = State( 'L X+50 Y-30 Z+150 R0 FMAX' )
    r = Parse( q )
  print( time.time() - start )
  print(q.stack)
  print(r)
  
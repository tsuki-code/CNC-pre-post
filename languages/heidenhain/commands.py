from enum import IntEnum, unique

class setval: # Setval(B, A) -> B = A
  def __init__( self, attribute, value ):
    self.attribute = attribute
    self.value = value
  def __call__( self, state ):
    state.symtable[self.attribute] = self.value
  def __repr__( self ):
    return 'setval: '+self.attribute.__repr__()+' = '+self.value.__repr__()

class Set:  # A Set(B) -> B = A
  def __init__(self, attribute):
    self.attribute = attribute
    
  def __call__( self, state ):
    state.symtable[self.attribute] = state.stack[-1]
    del state.stack[-1]
    
  def __repr__( self ):
    return 'Set (' + self.attribute.__repr__() + ')'
    
def discard( state ): # DISCARD STATE BUFFER
  del state.stack[:]

def invariant( state ): # UPDATE STATE GIVEN INVARIANT
  pass
  
class Temporary:  # SET REGISTER VALUE AS TEMPORARY AND RESTORE IT AFTER INVARIANT
  def __init__(self, attribute ):
    self.attribute = attribute
    
  def __call__( self, state ):
    state.symtable['temporary'] = self.attribute
  
  def __repr__( self ):
    return 'Temporary: '+self.attribute.__repr__()
    
def stop( state ):  # PROGRAM STOP
  pass
  
def optionalStop( state ):  # PROGRAM OPTIONAL STOP
  pass

def toolchange( state ):  # CHANGE TOOL TO Registers.TOOLNO
  pass
  
def end( state ): # END PROGRAM
  pass
  
@unique
class Registers(IntEnum):
  COMPENSATION = 0   # COMPENSATION TYPE
  DIRECTION    = 1   # CIRCLE DIRECTION
  LINENO       = 2   # LINE NUMBER
  UNITS        = 3   # MACHINE UNITS
  FEED         = 4   # MACHINE FEED
  SPINSPEED    = 5   # SPINDLE SPEED
  SPINDIR      = 6   # SPINDLE ROTATION DIRECTION
  MOTIONMODE   = 7   # POSITIONING MOTION MODE
  TOOLNO       = 8   # TOOL NUMBER
  TOOLDL       = 9   # TOOL DELTA LENGTH
  TOOLDR       = 10  # TOOL DELTA RADIUS
  COOLANT      = 11  # COOLANT TYPE
  WCS          = 12  # WORLD COORDINATE SYSTEM NUMBER

  
@unique
class Cartesian(IntEnum):
  # ABSOLUTE
  X = 13
  Y = 14
  Z = 15
  # INCREMENTAL
  XINC   = 16
  YINC   = 17
  ZINC   = 18
  
@unique
class Polar(IntEnum):
  # ABSOLUTE
  ANG = 19
  RAD = 20
  # INCREMENTAL
  ANGINC = 21
  RADINC = 22
  
@unique
class Angular(IntEnum):
  # ABSOLUTE
  A = 23
  B = 24
  C = 25
  # INCREMENTAL
  AINC   = 26
  BINC   = 27
  CINC   = 28

@unique
class Center(IntEnum): # CIRCLE CENTER X Y Z
  X = 29
  Y = 30
  Z = 31
  XINC  = 32
  YINC  = 33
  ZINC  = 34
  
 

incmap = { 
  Cartesian.X : Cartesian.XINC, Cartesian.Y : Cartesian.YINC, Cartesian.Z : Cartesian.ZINC, 
  Polar.ANG : Polar.ANGINC, Polar.RAD : Polar.RADINC,
  Angular.A : Angular.AINC, Angular.B : Angular.BINC, Angular.C : Angular.CINC, 
  Center.X : Center.XINC, Center.Y : Center.YINC, Center.Z : Center.ZINC
}
  
 
@unique
class Units(IntEnum):
  MM    = 0
  INCH  = 1
  
@unique
class Compensation(IntEnum):
  NONE = 0
  LEFT = 1
  RIGHT = 2

@unique
class Direction(IntEnum):
  CW = 0
  CCW = 1
  
@unique
class Motion(IntEnum):
  LINEAR = 0
  CIRCULAR = 1
  
@unique
class Coolant(IntEnum):
  OFF   = 0
  FLOOD = 1
  MIST  = 2
  AIR   = 3
  
@unique
class Spindle(IntEnum):
  OFF = 0
  CW  = 1
  CCW = 2
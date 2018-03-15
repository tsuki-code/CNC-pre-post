import generator.visitor as vis
from copy import copy

class ParserFailedType:
  pass
  
ParserFailed = ParserFailedType()

def _failure( result, success ):
  # return not success or result is ParserFailed
  return result is ParserFailed

class ParseVisitor(vis.Visitor):
  def __init__( self, lexer, handlers, defaultHandler ):
    self.handlers = handlers
    self.defaultHandler = defaultHandler
    self.table = {}
    self.lexer = lexer
    self.result = []
  
  def _handle( self, rule, result ):
    return self.handlers.get(rule, self.defaultHandler)(result)
    
  def _fork( self ):
    frk = ParseVisitor( self.lexer.fork(), self.handlers, self.defaultHandler )
    frk.result = self.result[:]
    frk.table = copy(self.table)
    return frk
  
  def _join( self, frk ):
    self.lexer.join( frk.lexer )
    self.result = frk.result
    frk.result = []
    self.table = frk.table
    frk.table = {}
    
  def Parser( self, visited ):
    result, stack = visited( self.lexer )
    self.result += stack
    return result
  
  def Handle( self, visited ):
    result = self.visit( visited.rule )
    
    if _failure(result, self.lexer.success):
      return ParserFailed
    
    return self._handle(visited, result)
    
  def Not( self, visited ):
    result = self.visit( visited.rule )
    
    if not _failure(result, self.lexer.success):
      return ParserFailed
    
    return self._handle( visited, None )
    
  def Optional( self, visited ):
    fork = self._fork()
    result = fork.visit( visited.rule )
    if _failure(result, fork.lexer.success ):
      return self._handle( visited, None )
    
    self._join( fork )
    return self._handle( visited, result )
    
  def Alternative( self, visited ):    
    result = ParserFailed
    for rule in visited.options:
      fork = self._fork()
      result = fork.visit( rule )
      if not _failure(result, fork.lexer.success):
        self._join( fork )
        break
    # debug_print( str(self) + " " + str(not _failure(result, lexer.success)) + " / " + lexer._input )
    result = self._handle(visited, result) if result is not ParserFailed else ParserFailed
    return result
    
  def Sequence( self, visited ):
    sequence = []
    for rule in visited.sequence:
      result = self.visit( rule )
      if _failure(result, self.lexer.success): 
        # debug_print( str(self) + " " + str(not _failure(result, lexer.success)) + " / " + lexer._input )
        return ParserFailed
      if result is not None:
        sequence += result
    
    # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
    return self._handle(visited, sequence)
    
  def Repeat( self, visited ):
    fork = self._fork()
    sequence = []
    while True:
      result = fork.visit( visited.rule )
      if _failure(result, fork.lexer.success):
        self._join( fork )
        # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
        return self._handle(visited, sequence)
      if result is not None:
        sequence += result 
      
  def Terminal( self, visited):
    #get a token from lexer, see if lexing failed
    token = self.lexer.get( visited.task )
    token = ParserFailed if token is None else token
      #return if error or EOL
    if _failure(token, self.lexer.success):
      # debug_print( str(self) + " " + str(not _failure(token, lexer.success)) + " / " + lexer._input )
      return ParserFailed
      # handle the token and return the result
    # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
    return [ self._handle(visited, token) ]
  
  def TerminalString( self, visited ):
    return self.Terminal( visited )
    
  def Always( self, visited ):
    return self._handle( visited, None)
  
  def Never( self, visited ):
    return ParserFailed
    
  def Ignore( self, visited ):
    result = self.visit( visited.rule )
    if _failure( result, self.lexer.success ):
      return ParserFailed
    else:      
      return self._handle( visited, None )
  
  def Push( self, visited ):
    result = self.visit( visited.rule )
    if not _failure( result, self.lexer.success ):
      if result is not None: 
        self.result.append( self._handle( visited, result ) )
      return None
    else:
      return ParserFailed
      
  def Copy( self, visited ):
    result = self.visit( visited.rule )
    if result is not ParserFailed:
      self.table[visited.name] = result
    return result
    
  def Cut( self, visited ):
    result = self.visit( visited.rule )
    if result is not ParserFailed:
      self.table[visited.name] = result
    return self._handle( visited, None )
    
  def Paste( self, visited ):
    if visited.name in self.table:
      return self.table[ visited.name ]
    return ParserFailed

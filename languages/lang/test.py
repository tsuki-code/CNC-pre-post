import languages.lang.grammar as g
import languages.lang.parser as p
import generator.state as s

def parse( input ):
  state = s.State( input )
  p.Parse( state )
  return state
  
def parseMultiline( input ):
  state = s.State('')
  for line in input.splitlines():
    state.input = line
    p.Parse( state )
  return state
    

test = (  parse("a = 'test'"), 
          parse("a = 'test' 'best'"), 
          parse("a = 'test' 'best' / 'detest'"),
          parse("a = a"),
          parse("a = *a 'das'"),
          parse("a = *( ?'das' 'das' / 'ssd' ) a"),
          parse("a = 'dsa' / 'dds' / 'asd'")
          )

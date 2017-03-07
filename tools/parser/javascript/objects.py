from .constants import *
from .util import *

class JSObject(object):
    '''
    Parent information holder class
    '''
    def __init__(self, start):
        self.inBody = True
        self.start = start

    def end(self, end):
        self.endpoint = end

class Variable(JSObject):
    '''
    Variable information holder class
    '''
    def __init__(self, start):
        JSObject.__init__(self, start)
        self.name = "#undeclared#"
        self.value = None

    def setName(self, name):
        self.name = name

    def setValue(self, value):
        self.value = value

    def toObject(self):
        obj = {
            "type": "variable",
            "name": self.name
        }
        if isinstance(self.value, (Function, Container, Array, Expression, Regex)):
            obj["value"] = self.value.toObject()
        else:
            obj["value"] = str(self.value)

        return obj

    def __repr__(self):
        return self.name+":"+str(self.value)

class Function(JSObject):
    '''
    Function information holder class
    '''
    def __init__(self, start):
        JSObject.__init__(self, start)
        self.args = []
        self.inBody = False
        self.name = "#anonymous#"
        self.returned = []
        self.expressions = []

    def addArgument(self, parser, arg):
        self.args.append(arg)

        ptr = parser.ptr
        # move to comma or end of args
        ptr.whitespace()
        if ptr.current() == ')':
            self.inBody = True
            ptr.whitespace(after=True)
            if ptr.current() != '{':
                raise ParseError("Text between args and body", parser)

    def addExpression(self, expr):
        self.expressions.append(expr)

    def setName(self, name):
        self.name = name

    def addReturn(self, returned):
        self.returned.append(returned)

    def toObject(self):
        obj = {
            "type": "function",
            "name": self.name,
            "returned": [],
            "expressions": []
        }
        for r in self.returned:
            obj["returned"].append(r.toObject())
        for e in self.expressions:
            if isinstance(e, (Function, Variable, Container, Array, Expression, Regex, Logic)):
                obj["expressions"].append(e.toObject())
            else:
                obj["expressions"].append(str(e))

        return obj

    def __repr__(self):
        return self.name+"("+str(self.args)+"):returns "+str(self.returned)

class Container(JSObject):
    '''
    Javascript object information holder class
    '''
    def __init__(self, start):
        JSObject.__init__(self, start)
        self.inBody = False
        self.keys = []
        self.values = []


    def addKey(self, parser, key):
        self.keys.append(key)

        ptr = parser.ptr
        # move to colon
        ptr.whitespace()
        if ptr.current() != ':':
            raise ParseError("Text between key and colon", parser)

        self.inBody = True
    def addValue(self, parser, value):
        self.values.append(value)

        ptr = parser.ptr
        # move to comma or end of object
        ptr.whitespace()
        if ptr.current() == '}':
            return True # ready to declare
        elif ptr.current() != ',':
            raise ParseError("No comma before next key", parser)

        self.inBody = False

    def toObject(self):
        obj = {
            "type": "object",
            "keys": [],
            "values": []
        }
        for k in self.keys:
            if isinstance(k, (Function, Container, Array, Expression, Regex)):
                obj["keys"].append(k.toObject())
            else:
                obj["keys"].append(str(k))
        for v in self.values:
            if isinstance(v, (Function, Container, Array, Expression, Regex)):
                obj["values"].append(v.toObject())
            else:
                obj["values"].append(str(v))

        return obj
        
    def __repr__(self):
        return str(self.keys)+": "+str(self.values)
    
class Array(JSObject):
    '''
    Array information holder class
    '''
    def __init__(self, start):
        JSObject.__init__(self, start)
        self.elements = []
    
    def addElement(self, parser, value):
        self.elements.append(value)

        ptr = parser.ptr
        # move to comma or end of array
        ptr.whitespace()
        if ptr.current() == ']':
            return True # ready to declare
        elif ptr.current() != ',':
            raise ParseError("Invalid array declaration", parser)

    def toObject(self):
        obj = {
            "type": "array",
            "elements": []
        }
        for e in self.elements:
            if isinstance(e, (Function, Container, Array, Expression, Regex)):
                obj["elements"].append(v.toObject())
            else:
                obj["elements"].append(str(v))

        return obj

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.elements)

class Logic(JSObject):
    '''
    Information holder for logic
    '''
    def __init__(self, start, name):
        JSObject.__init__(self, start)
        self.inBody = False
        self.expressions = []
        self.condition = None
        self.name = name

    def addExpression(self, expr):
        self.expressions.append(expr)

    def setCondition(self, cond):
        self.condition = cond

    def toObject(self):
        obj = {
            "type": "logic",
            "logic": self.name,
            "expressions": []
        }

        if isinstance(self.condition, Expression):
            obj["condition"] = self.condition.toObject()
        else:
            obj["condition"] = str(self.condition)

        for e in self.expressions:
            if isinstance(e, (Function, Variable, Container, Array, Expression, Regex, Logic)):
                obj["expressions"].append(e.toObject())
            else:
                obj["expressions"].append(str(e))

        return obj

    def __repr__(self):
        return str(self.name) + "(" + str(self.condition) + ")" + "{}"

class Expression(JSObject):
    '''
    General expression info holder
    '''
    def __init__(self, start, values):
        JSObject.__init__(self, start)
        self.values = values

    def isValid(self):
        return (not self.values[-1] in ASSIGNMENT) and self.closable()
        
    def closable(self):
        return self.parenBalance() + self.bracketBalance() == 0

    def parenBalance(self):
        count = 0
        for val in self.values:
            if isinstance(val, str):
                count += val.count('(') - val.count(')')
        return count

    def bracketBalance(self):
        count = 0
        for val in self.values:
            if isinstance(val, str):
                count += val.count('[') - val.count(']')
        return count
    
    def addValue(self, value):
        self.values.append(value)

    def toObject(self):
        obj = {
            "type": "expression",
            "values": []
        }
        temp = ""
        for v in self.values:
            if isinstance(v, (Function, Variable, Container, Array, Expression, Regex, Logic)):
                obj["values"].append(temp)
                temp = ""
                obj["values"].append(v.toObject())
            else:
                temp += str(v)
        obj["values"].append(temp)
        return obj
        
    def __repr__(self):
        return str(self.values)

class Return(JSObject):
    '''
    Return block info holder
    '''
    def __init__(self, start):
        JSObject.__init__(self, start)
        self.expression = [];

    def addChild(self, value):
        self.expression.append(value)

    def toObject(self):
        obj = {
            "type": "return",
            "expression": []
        }

        for e in self.expression:
            if isinstance(e, (Function, Variable, Container, Array, Expression, Regex, Logic)):
                obj["expression"].append(e.toObject())
            else:
                obj["expression"].append(str(e))

        return obj

    def __repr__(self):
        return str(self.expression)

class Regex(JSObject):
    '''
    Regex info holder
    '''
    def __init__(self, start, expr=None):
        JSObject.__init__(self, start)
        self.expression = expr

    def setExpression(self, expr):
        self.expression = expr

    def toObject(self):
        obj = {
            "type": "regex",
            "expression": expr
        }


        return obj
        
    def __repr__(self):
        return str(self.expression)

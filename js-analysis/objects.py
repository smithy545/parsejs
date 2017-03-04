from constants import *
from util import *

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

    def __repr__(self):
        return self.__str__()

    def __str__(self):
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
        self.returned = None
        self.expressions = []

    def addArgument(self, ptr, arg):
        self.args.append(arg)

        # move to comma or end of args
        ptr.whitespace()
        if ptr.current() == ')':
            self.inBody = True
            ptr.whitespace(after=True)
            if ptr.current() != '{':
                raise ParseException("Text between args and body")

    def addExpression(self, expr):
        self.expressions.append(expr)

    def setName(self, name):
        self.name = name

    def setReturn(self, returned):
        self.returned = returned

    def __repr__(self):
        return self.__str__()

    def __str__(self):
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


    def addKey(self, ptr, key):
        self.keys.append(key)

        # move to colon
        ptr.whitespace()
        if ptr.current() != ':':
            raise ParseException("Text between key and colon", ptr)

        self.inBody = True
    def addValue(self, ptr, value):
        self.values.append(value)

        # move to comma or end of object
        ptr.whitespace()
        if ptr.current() == '}':
            return True # ready to declare
        elif ptr.current() != ',':
            raise ParseException("No comma before next key", ptr)

        self.inBody = False
        
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.keys)+": "+str(self.values)
    
class Array(JSObject):
    '''
    Array information holder class
    '''
    def __init__(self, start):
        JSObject.__init__(self, start)
        self.elements = []
    
    def addElement(self, ptr, value):
        self.elements.append(value)

        # move to comma or end of array
        ptr.whitespace()
        if ptr.current() == ']':
            return True # ready to declare

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
        self.name = name
        self.expressions = []
        self.condition = None

    def addExpression(self, expr):
        self.expressions.append(expr)

    def setCondition(self, cond):
        self.condition = cond
        
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
        
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.values)

class ReturnBlock(JSObject):
    '''
    Return block info holder
    '''
    def __init__(self, start):
        JSObject.__init__(self, start)
        self.expression = [];

    def addChild(self, value):
        self.expression.append(value)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.expression)

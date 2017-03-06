from .tokens import *
from .objects import *
from .constants import *
from .util import *

class Parser(object):
    def __init__(self, text):
        self.ptr = Pointer(text)
        self.declared = []
        self.stack = []

    def organize(self):
        pass

    def declare(self):
        stack = self.stack
        declared = self.declared
        ptr = self.ptr

        if len(stack) < 1:
            raise ParseError("Tried to declare on empty stack", self)
        elif isinstance(stack[-1], Return): # pop off stack but don't declare
            block = stack.pop()
            for obj in reversed(stack):
                if isinstance(obj, Function):
                    obj.addReturn(block)
                    return
                elif not isinstance(obj, Logic):
                    raise ParseError("Invalid return statement placement", self)
            raise ParseError("Functionless return statement", self)

        # close and declare child
        child = stack.pop()
        child.end(ptr.createToken())

        # if stack not empty add child to parent
        if len(stack) > 0:
            ptr.next() # move beyond end of child
            parent = stack[-1]
            if isinstance(parent, Function):
                if parent.inBody:
                    parent.addExpression(child)
                    ptr.previous() # return to end of child
                else:
                    parent.addArgument(self, child)
            elif isinstance(parent, Array):
                if parent.addElement(self, child):
                    self.declare() # declare recursively
            elif isinstance(parent, Container):
                if parent.inBody:
                    if parent.addValue(self, child):
                        self.declare() # declare recursively
                else:
                    parent.addKey(self, child)
            elif isinstance(parent, Variable):
                parent.setValue(child)
                self.declare() # declare recursively
                if ptr.current() == ',': # TODO: move this into function to reduce duplicate code
                    v = Variable(ptr.createToken())

                    ptr.whitespace(after=True) # move past whitespace
                    
                    if not validNameStart(ptr.current()): # check for variable name
                        raise ParseError("Invalid variable declaration: invalid variable name", self)

                    # parse until whitespace or equals sign for varname
                    varname = ptr.untilNot(VALID_VARIABLE, after=False)
                    
                    v.setName(varname)
                    ptr.whitespace()

                    stack.append(v)
                    if ptr.current() == ',' or ptr.current() == ';' or (ptr.current()+ptr.peek()) == 'in':
                        self.declare()
                    elif ptr.current() != '=':
                        raise ParseError("Invalid variable declaration: text between name and =", self)

            elif isinstance(parent, Expression):
                parent.addValue(child)
                ptr.previous() # return to end of child
            elif isinstance(parent, Return):
                parent.addChild(child)
                ptr.previous() # return to end of child
            elif isinstance(parent, Logic):
                ptr.previous() # return to end of child
                if parent.inBody:
                    parent.addExpression(child)
                else:
                    parent.setCondition(child)
            else:
                declared.append(child) # if not contained declare it
                ptr.previous() # return if no recursive declaration
        else:
            declared.append(child) # if empty stack declare it

    def parse(self):
        declared = self.declared
        stack = self.stack
        ptr = self.ptr

        c = ptr.next()
        while c != None:
            if c == "/": # is it a comment or regex
                delim = ptr.peek()
                if delim != None:
                    if delim == '/':
                        ptr.until('\n')
                        c = ptr.next()
                        continue
                    elif delim == '*':
                        ptr.until('*/')
                        c = ptr.next()
                        continue
                    else:
                        getRegex(ptr)

            if c in VALID_VARIABLE: # is it a valid variable char
                kw = ptr.checkKeyword()
                if kw: # is it a keyword
                    if kw == 'function': # function declaration
                        if len(stack) > 0:
                            parent = stack[-1]
                            if isinstance(parent, Container):
                                if not parent.inBody:
                                    raise ParseError("Cannot declare function as object key", self)

                        self.getFunction()
                    elif kw in ['var', 'let', 'const']: # variable declaration
                        if len(stack) > 0:
                            parent = stack[-1]
                            if isinstance(parent, Function):
                                if not parent.inBody:
                                    raise ParseError("Cannot declare variable in function arguments", self)
                            elif isinstance(parent, Container):
                                raise ParseError("Cannot declare variable in object", self)
                            elif isinstance(parent, Array):
                                raise ParseError("Cannot declare variable in array", self)
                            elif isinstance(parent, Logic):
                                if parent.name != 'for':
                                    raise ParseError("Cannot declare variable in logic statement", self)

                        self.getVariable(kw)
                    elif kw == 'return': # return statement
                        if len(stack) > 0:
                            parent = stack[-1]
                            if isinstance(parent, Array):
                                raise ParseError("Return statement in array")
                            elif isinstance(parent, Container):
                                raise ParseError("Return statement in container")
                            elif isinstance(parent, Variable):
                                raise ParseError("Return statement in variable")
                    
                        self.getReturn()
                    elif kw in ['if', 'while', 'for', 'else']: # logic statement
                        if len(stack) > 0:
                            parent = stack[-1]
                            if isinstance(parent, Function):
                                if not parent.inBody:
                                    raise ParseError("Logic block in function arguments", self)
                            elif isinstance(parent, Container):
                                raise ParseError("Logic block in object", self)
                            elif isinstance(parent, Array):
                                raise ParseError("Logic block in array", self)
                            elif isinstance(parent, Variable):
                                raise ParseError("Logic block in variable declaration", self)

                        self.getLogic(kw)
                    elif kw == 'try': # error handling
                        if len(stack) > 0:
                            parent = stack[-1]
                            if isinstance(parent, Function):
                                if not parent.inBody:
                                    raise ParseError("Try/Catch block in function arguments", self)
                            elif isinstance(parent, Container):
                                raise ParseError("Try/Catch block in object", self)
                            elif isinstance(parent, Array):
                                raise ParseError("Try/Catch block in array", self)
                            elif isinstance(parent, Variable):
                                raise ParseError("Try/Catch block in variable declaration", self)

                        self.getTry()
                    elif kw == 'case':# handle switch cases
                        if len(stack) < 1 or\
                        not (isinstance(stack[-1], Logic) and stack[-1].name == 'switch'): # must be in switch
                            raise ParseError("Case outside of switch statement", self)

                        self.getCase()
                    else:
                        kw = None
                if kw == None: # handle other
                    e = self.getExpression()
                    stack.append(e)
                    if ptr.current() in '[(':
                        e.addValue(ptr.current())
                    elif e.isValid():
                        ptr.previous() # return to just before delimiter
                        self.declare() # declare expression
                    else:
                        ptr.previous()
            elif c == '(': # start of new expression
                stack.append(Expression(ptr.createToken(), ['(']))
            elif c == ')':
                if len(stack) > 0:
                    parent = stack[-1]
                    if isinstance(parent, Logic): # closing the logic condition
                        parent.inBody = True
                        ptr.whitespace(after=True)
                        oneliner = ptr.until(['{', '\n'], after=False)
                        if ptr.current() != '{': # one line logic
                            stack.append(self.getExpression(Pointer(oneliner))) # one line logic
                            self.declare() # declare expression
                            self.declare() # declare logic
                    elif isinstance(parent, Expression):
                        bal = parent.parenBalance()
                        if bal > 0: # if normal paren just add it
                            parent.addValue(c)
                        elif bal < 0: # if extra paren expression broken
                            raise ParseError("Unbalanced parens in expression", self)
                        else: # declare if hitting external paren
                            if parent.isValid():
                                ptr.previous() # move to end of child
                                self.declare() # declare expression
                            else:
                                raise ParseError("Declaring invalid expression: after )", self)
                    else:
                        raise ParseError("Unbalanced parens", self)
                else:
                    raise ParseError("Unbalanced parens: empty stack", self)
            elif c == '[': # start of new array
                stack.append(Array(ptr.createToken()))
            elif c == ']':
                if len(stack) > 0:
                    parent = stack[-1]
                    if isinstance(parent, Array): # end of array
                        self.declare() # declare array
                    elif isinstance(parent, Expression):
                        bal = parent.bracketBalance()
                        if bal > 0: # if normal bracket just add it
                            parent.addValue(c)
                        elif bal < 0: # if extra bracket expression broken
                            raise ParseError("Unbalanced brackets in expression", self)
                        else: # declare if hitting external bracket
                            if parent.isValid():
                                ptr.previous() # move to end of child
                                self.declare() # declare expression
                            else:
                                raise ParseError("Invalid expression declared: at ]", self)
                    else:
                        raise ParseError("Unbalanced square brackets: improper parent", self)
                else:
                    raise ParseError("Unbalanced square brackets: empty stack", self)
            elif c == '{': # start of new object (assume no blocks for now cause fuck me if there are blocks)
                stack.append(Container(ptr.createToken()))
            elif c == '}':
                if len(stack) > 0:
                    parent = stack[-1]
                    if isinstance(parent, Function): # end of function
                        if not parent.inBody:
                            raise ParseError("} in function args", self)
                        self.declare() # declare function
                    elif isinstance(parent, Container): # end of object
                        self.declare() # declare object
                    elif isinstance(parent, Logic): # end of logic block
                        self.declare() # kill logic block
                    elif isinstance(parent, Expression):
                        if parent.isValid():
                            ptr.previous() # move to end of child
                            self.declare() # declare expression
                        else:
                            raise ParseError("Closing brace in expression", self)
                    elif isinstance(parent, Return):
                        self.declare() # kill return block
                        ptr.previous() # return for second pass
                else:
                    raise ParseError("Unbalanced curly braces: empty stack", self)
            elif c == "'" or c == '"': # handle quote
                self.getQuote()
            elif c == ';':
                if len(stack) > 0:
                    parent = stack[-1]
                    if isinstance(parent, Expression): # end expression
                        if parent.isValid():
                            self.declare() # declare expression
                            ptr.previous() # return for second pass
                        else:
                            raise ParseError("Closing invalid expression: semicolon", self)
                    elif isinstance(parent, Return):
                        self.declare() # kill return block
            elif c == ',':
                if len(stack) > 0:
                    parent = stack[-1]
                    if isinstance(parent, Expression):
                        if parent.isValid():
                            self.declare()
                        else:
                            parent.addValue(',')
                else:
                    raise ParseError("Lonely comma", self)
            elif c in '=*/+-|&^%': # possible start of assignment
                if c == '=' and ptr.peek() == '>': # arrow function
                    if len(stack) > 0 and isinstance(stack[-1], Expression):
                        parent = stack.pop()
                        f = Function(parent.start)

                        for val in parent.values[1:-1]: # ignore parens
                            if val != ',':
                                f.args.append(val)

                        ptr.skip(len('=>')) # skip arrow
                        ptr.whitespace() # skip to {

                        if ptr.current() != '{':
                            raise ParseError("Invalid arrow function declaration", self)
                        f.inBody = True
                        self.stack.append(f)
                    else:
                        raise ParseError("=> with no args", self)
                else: # assignment function
                    self.getAssignment()
            c = ptr.next()

        if len(stack) > 0:
            raise ParseError("Items remaining on stack", self)
        
        self.organize() # organize declared objects

        return declared

    def getExpression(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        values = []
        start = ptr.createToken()

        value = ptr.untilNot(VALID_VARIABLE, after=False)
        if value == 'new' or value == 'throw' or value == 'delete':
            ptr.whitespace()
            value += ' ' + ptr.untilNot(VALID_VARIABLE, after=False)
        values.append(value)
        ptr.whitespace()
        op = ptr.check(OPERATORS.union(['instanceof', 'in']))
        while op:
            if op == '/':
                c = ptr.peek()
                if c == '/':
                    ptr.until('\n')
                    continue
                elif c == '*':
                    ptr.until('*/')
                    continue
            values.append(op)
            ptr.skip(len(op))
            ptr.whitespace()
            value = ptr.untilNot(VALID_VARIABLE, after=False)
            if len(value) > 0:
                if value == 'new' or value == 'throw' or value == 'delete':
                    ptr.whitespace()
                    value += ' ' + ptr.untilNot(VALID_VARIABLE, after=False)
                for kws in KEYWORDS:
                    if value in kws:
                        ptr.skip(-len(value))
                        return values
                values.append(value)
            ptr.whitespace()
            op = ptr.check(OPERATORS.union(['instanceof', 'in']))

        return Expression(start, values)

    def getAssignment(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        op = ptr.check(ASSIGNMENT)
        if op:
            if len(self.stack) > 0 and isinstance(self.stack[-1], Expression):
                parent.addValue(op)
            else:
                raise ParseError("Lonely assignment", self)

    def getQuote(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        c = ptr.current()
        self.stack.append(Expression(ptr.createToken(), [c+ptr.until(c)+c]))
        self.declare()

    def getRegex(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        pass

    def getLogic(self, kw, ptr=None):
        if ptr == None:
            ptr = self.ptr

        self.stack.append(Logic(ptr.createToken(), kw))

        ptr.skip(len(kw)) # move past keyword
        ptr.whitespace() # move past whitespace

        if kw == 'else':
            if ptr.current() == 'i': # else if statement
                ptr.next() # skip past if
                ptr.whitespace(after=True)
                if ptr.current() != '(':
                    raise ParseError("Text between if and (", self)
            elif ptr.current() == '{': # else no if
                self.stack[-1].inBody = True
            else: # one line else
                oneliner = ptr.until('\n', after=False)
                self.stack.append(self.getExpression(Pointer(oneliner)))
                self.declare() # declare expression
                self.declare() # declare else
        elif ptr.current() != '(': # invalid if/while/for/switch
            raise ParseError("Text between logic and (", self)

    def getCase(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        pass

    def getTry(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        ptr.skip(len('try'))
        ptr.whitespace()

        if ptr.current() == '{':
            self.stack[-1].inBody = True
        else: # one line try
            oneliner = ptr.until('\n', after=False)
            self.stack.append(self.getExpression(Pointer(oneliner)))
            self.declare() # declare expression
            self.declare() # declare try


    def getFunction(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        f = Function(ptr.createToken())
                        
        ptr.skip(len('function')) # move past 'function'
        ptr.whitespace() # move past whitespace
        
        if validNameStart(ptr.current()): # find function name if any
            name = ptr.untilNot(VALID_VARIABLE, after = False)
            f.setName(name)
            ptr.whitespace()
            
        if ptr.current() != '(': # if arguments don't start
            raise ParseError("Invalid function syntax", ptr, self.stack)
        
        # check for empty args
        ptr.whitespace(after=True)
        if ptr.current() == ')': # no args, just go right to body
            f.inBody = True
            ptr.whitespace(after=True)
            if ptr.current() != '{':
                raise ParseError("Text between function and {", ptr, self.stack)
        else:
            ptr.previous() # previous to allow parsing if args found
            
        self.stack.append(f)

    def getVariable(self, kw, ptr=None):
        if ptr == None:
            ptr = self.ptr

        v = Variable(ptr.createToken())

        ptr.skip(len(kw)) # move past keyword
        ptr.whitespace() # move past whitespace
        
        if not validNameStart(ptr.current()): # check for variable name
            raise ParseError("Invalid variable declaration: invalid variable name", self)

        # parse until whitespace or equals sign for varname
        varname = ptr.untilNot(VALID_VARIABLE, after=False)
        
        v.setName(varname)
        ptr.whitespace()

        self.stack.append(v)
        if ptr.current() == ',' or ptr.current() == ';' or (ptr.current()+ptr.peek()) == 'in':
            self.declare()
        elif ptr.current() != '=':
            raise ParseError("Invalid variable declaration: text between name and =", self)

    def getReturn(self, ptr=None):
        if ptr == None:
            ptr = self.ptr

        ptr.skip(len('return')-1) # move past keyword

        self.stack.append(Return(ptr.createToken()))

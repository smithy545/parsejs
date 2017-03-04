from tokens import *
from jsobjects import *
from constants import *

def declare(declared, stack, ptr):
    if len(stack) < 1:
        return
    elif isinstance(stack[-1], ReturnBlock): # pop off stack but don't declare
        block = stack.pop()
        for obj in reversed(stack):
            if isinstance(obj, Function):
                obj.returned = block
                return
            elif not isinstance(obj, Logic):
                raise ParseException("Invalid return statement placement", ptr, stack)
        raise ParseException("Functionless return statement", ptr, stack)

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
                parent.addArgument(ptr, child)
        elif isinstance(parent, Array):
            if parent.addElement(ptr, child):
                declare(declared, stack, ptr) # declare recursively
        elif isinstance(parent, Container):
            if parent.inBody:
                if parent.addValue(ptr, child):
                    declare(declared, stack, ptr) # declare recursively
            else:
                parent.addKey(ptr, child)
        elif isinstance(parent, Variable):
            parent.setValue(child)
            declare(declared, stack, ptr) # declare recursively
        elif isinstance(parent, Expression):
            parent.addValue(child)
            ptr.previous() # return to end of child
        elif isinstance(parent, ReturnBlock):
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

def analyze(filename):
    file = open(filename, 'r')

    ptr = Pointer(file.read())
    file.close()
    
    declared = []
    stack = []
    
    c = ptr.next()
    while c != None:
        if c == "/": # is it a comment
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
                
        if c in VALID_VARIABLE: # is it a valid variable char
            kw = ptr.checkKeyword()
            if kw: # is it a keyword
                if kw == 'function':
                    f = Function(ptr.createToken())
                    
                    ptr.skip(len(kw)) # move past 'function'
                    ptr.whitespace() # move past whitespace
                    
                    if validNameStart(ptr.current()): # find function name if any
                        name = ptr.untilNot(VALID_VARIABLE, after = False)
                        f.setName(name)
                        ptr.whitespace()
                        
                    if ptr.current() != '(': # if arguments don't start
                        raise ParseException("Invalid function syntax", ptr, stack)
                    
                    # check for empty args
                    ptr.whitespace(after=True)
                    if ptr.current() == ')': # no args, just go right to body
                        f.inBody = True
                        ptr.whitespace(after=True)
                        if ptr.current() != '{':
                            raise ParseException("Text between function and {", ptr, stack)
                    else:
                        ptr.previous() # previous to allow parsing if args found
                        
                    stack.append(f)
                elif kw == 'var' or kw == 'let' or kw == 'const':
                    if len(stack) > 0:
                        parent = stack[-1]
                        if isinstance(parent, Function):
                            if not parent.inBody:
                                raise ParseException("Cannot declare variable in function arguments", ptr, stack)
                        elif isinstance(parent, Container):
                            raise ParseException("Cannot declare variable in object", ptr, stack)
                        elif isinstance(parent, Array):
                            raise ParseException("Cannot declare variable in array", ptr, stack)

                    v = Variable(ptr.createToken())

                    ptr.skip(len(kw)) # move past keyword
                    ptr.whitespace() # move past whitespace
                    
                    if not validNameStart(ptr.current()): # check for variable name
                        raise ParseException("Invalid variable declaration: invalid variable name", ptr, stack)

                    # parse until whitespace or equals sign for varname
                    varname = ptr.untilNot(VALID_VARIABLE, after=False)
                    
                    v.setName(varname)
                    ptr.whitespace()

                    stack.append(v)
                    if ptr.current() == ',' or ptr.current() == ';':
                        declare(declared, stack, ptr)
                    elif ptr.current() != '=':
                        raise ParseException("Invalid variable declaration: text between name and =", ptr, stack)

                elif kw == 'if' or kw == 'while' or kw == 'for' or kw == 'else' or kw == 'try' or kw == 'catch' or kw == 'switch':
                    if len(stack) > 0:
                        parent = stack[-1]
                        if isinstance(parent, Function):
                            if not parent.inBody:
                                raise ParseException("Logic block in function arguments", ptr, stack)
                        elif isinstance(parent, Container):
                            raise ParseException("Logic block in object", ptr, stack)
                        elif isinstance(parent, Array):
                            raise ParseException("Logic block in array", ptr, stack)
                        elif isinstance(parent, Variable):
                            raise ParseException("Logic block in variable declaration", ptr, stack)

                    stack.append(Logic(ptr.createToken(), kw))

                    ptr.skip(len(kw)) # move past keyword
                    ptr.whitespace() # move past whitespace

                    if kw == 'else':
                        if ptr.current() == 'i': # else if statement
                            ptr.next() # skip past if
                            ptr.whitespace(after=True)
                            if ptr.current() != '(':
                                raise ParseException("Text between if and (", ptr, stack)
                        elif ptr.current() == '{': # else no if
                            stack[-1].inBody = True
                        else: # invalid else
                            raise ParseException("Text after else", ptr, stack)
                    elif kw == 'try':
                        if ptr.current() == '{':
                            stack[-1].inBody = True
                        else:
                            raise ParseException("Text after try", ptr, stack)
                    elif ptr.current() != '(': # invalid if/while/for/catch/switch
                        raise ParseException("Text between logic and (", ptr, stack)
                elif kw == 'return':
                    if len(stack) > 0:
                        parent = stack[-1]
                        if isinstance(parent, Array):
                            raise ParseException("Return statement in array")
                        elif isinstance(parent, Container):
                            raise ParseException("Return statement in container")
                        elif isinstance(parent, Variable):
                            raise ParseException("Return statement in variable")
                    
                    ptr.skip(len(kw)-1) # move past keyword

                    stack.append(ReturnBlock(ptr.createToken()))
                else:
                    kw = None
            if kw == None: # handle other
                e = Expression(ptr.createToken(), ptr.getExpression())
                stack.append(e)
                if ptr.current() in '[(':
                    e.addValue(ptr.current())
                elif e.isValid():
                    ptr.previous() # return to just before delimiter
                    declare(declared, stack, ptr) # declare expression
                else:
                    ptr.previous()
        elif c == '(':
            e = Expression(ptr.createToken(), ['('])
            stack.append(e)
        elif c == ')':
            if len(stack) > 0:
                parent = stack[-1]
                if isinstance(parent, Logic):
                    parent.inBody = True
                    ptr.whitespace(after=True)
                    if ptr.current() != '{':
                        raise ParseException("Text between logic and {", ptr, stack)
                elif isinstance(parent, Expression):
                    bal = parent.parenBalance()
                    if bal > 0: # if normal paren just add it
                        parent.addValue(c)
                    elif bal < 0: # if extra paren expression broken
                        print(stack[-3:])
                        raise ParseException("Unbalanced parens in expression", ptr, stack)
                    else: # declare if hitting external paren
                        if parent.isValid():
                            ptr.previous() # move to end of child
                            declare(declared, stack, ptr) # declare expression
                            #ptr.next() # move back to paren
                        else:
                            raise ParseException("Declaring invalid expression: after )", ptr, stack)
                else:
                    raise ParseException("Unbalanced parens", ptr, stack)
            else:
                raise ParseException("Unbalanced parens: empty stack", ptr, stack)
        elif c == '[': # is it the start of an array
            stack.append(Array(ptr.createToken()))
        elif c == ']':
            if len(stack) > 0:
                parent = stack[-1]
                if isinstance(parent, Array):
                    declare(declared, stack, ptr) # declare array
                elif isinstance(parent, Expression):
                    bal = parent.bracketBalance()
                    if bal > 0: # if normal bracket just add it
                        parent.addValue(c)
                    elif bal < 0: # if extra bracket expression broken
                        raise ParseException("Unbalanced brackets in expression", ptr, stack)
                    else: # declare if hitting external bracket
                        if parent.isValid():
                            ptr.previous() # move to end of child
                            declare(declared, stack, ptr) # declare expression
                            #ptr.next() # move back to bracket
                        else:
                            raise ParseException("Invalid expression declared: at ]", ptr, stack)
                else:
                    raise ParseException("Unbalanced square brackets: improper parent", ptr, stack)
            else:
                raise ParseException("Unbalanced square brackets: empty stack", ptr, stack)
        elif c == '{': # is it the start of an object (assume no blocks for now cause fuck me if there are blocks)
            stack.append(Container(ptr.createToken()))
        elif c == '}': # is it the end of a function or object
            if len(stack) > 0:
                parent = stack[-1]
                if isinstance(parent, Function):
                    if not parent.inBody:
                        raise ParseException("} in function args", ptr, stack)
                    declare(declared, stack, ptr) # declare function
                elif isinstance(parent, Container):
                    declare(declared, stack, ptr) # declare object
                elif isinstance(parent, Logic):
                    declare(declared, stack, ptr) # kill logic block
                elif isinstance(parent, Expression):
                    if parent.isValid():
                        ptr.previous()
                        declare(declared, stack, ptr)
                    else:
                        raise ParseException("Closing brace in expression", ptr, stack)
                elif isinstance(parent, ReturnBlock):
                    declare(declared, stack, ptr) # kill return block
                    ptr.previous() # return for second pass
            else:
                raise ParseException("Unbalanced curly braces: empty stack", ptr, stack)
        elif c == "'" or c == '"': # handle quote
            value = ptr.until(c)
            if len(stack) > 0:
                parent = stack[-1]
                if isinstance(parent, Function):
                    if not parent.inBody:
                        ptr.next()
                        parent.addArgument(ptr, c+value+c)
                elif isinstance(parent, Container):
                    ptr.next()
                    if parent.inBody:
                        if parent.addValue(ptr, c+value+c):
                            declare(declared, stack, ptr) # declare expression
                    else:
                        parent.addKey(ptr, value)
                elif isinstance(parent, Variable):
                    parent.setValue(value)
                    declare(declared, stack, ptr) # declare variable
                elif isinstance(parent, Array):
                    ptr.next()
                    if parent.addElement(ptr, c+value+c):
                        declare(declared, stack, ptr) # declare array
                elif isinstance(parent, Expression):
                    parent.addValue(c+value+c)
        elif c == ';':
            if len(stack) > 0:
                parent = stack[-1]
                if isinstance(parent, Expression):
                    if parent.isValid():
                        declare(declared, stack, ptr)
                        ptr.previous() # return to parent expressions to declare
                    else:
                        raise ParseException("Closing invalid expression: semicolon", ptr, stack)
                elif isinstance(parent, ReturnBlock):
                    declare(declared, stack, ptr) # kill return block
        elif c == ',':
            if len(stack) > 0:
                parent = stack[-1]
                if isinstance(parent, Expression):
                    if parent.isValid():
                        declare(declared, stack, ptr)
                    else:
                        parent.addValue(',')
            else:
                raise ParseException("Lonely comma", ptr, stack)
        elif c in '=*/+-|&^%': # possible start of assignment
            op = ptr.check(ASSIGNMENT)
            if op:
                if len(stack) > 0:
                    parent = stack[-1]
                    if isinstance(parent, Expression):
                        parent.addValue(op)
                else:
                    raise ParseException("Lonely assignment", ptr, stack)
        else:
            if not c in WHITESPACE:
                #print(c)
                pass
        c = ptr.next()

    if len(stack) > 0:
        raise ParseException("Items remaining on stack", None, stack)
    
    return declared

objects = analyze('./test.js')

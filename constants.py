KEYWORDS = [
    set(['if', 'in', 'do']), # keywords of length 2
    set(['int', 'for', 'let', 'new', 'try', 'var']), # length 3
    set(['byte', 'case', 'char', 'else', 'enum', 'goto', 'long', 'null', 'this', 'true', 'void', 'with']), # and so on
    set(['super', 'break', 'false', 'throw', 'catch', 'final', 'class', 'float', 'const', 'short', 'while']),
    set(['switch', 'export', 'native', 'throws', 'typeof', 'public', 'delete', 'return', 'import', 'double', 'static']),
    set(['boolean', 'extends', 'finally', 'package', 'private', 'default']),
    set(['abstract', 'continue', 'function', 'debugger', 'volatile']),
    set(['interface', 'transient', 'protected']),
    set(['instanceof', 'implements']),
    set([]),
    set(['synchronized'])  # length 12
]

WHITESPACE = set([' ', '\n', '\t'])

COMPARISON = set(['==', '!=', '!==', '===', '<=', '>=', '&&', '||'])
UNARY = set(['++', '--', '!'])
BINARY = set(['+', '-', '*', '/', '%', '&', '^', '|', '.', '<', '>'])
ASSIGNMENT = set(['=', '*=', '/=', '+=', '-=', '|=', '&=', '^=', '%='])
OPERATORS = COMPARISON.union(UNARY).union(BINARY).union(ASSIGNMENT)


NUMBERS = set(['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'])

LOWERCASE = set(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'])
UPPERCASE = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
LETTERS = UPPERCASE.union(LOWERCASE)

VALID_VARIABLE_START = LETTERS.union(['$', '_'])
VALID_VARIABLE = LETTERS.union(NUMBERS).union(['$', '_'])

class ParseException(Exception):
    def __init__(self, message, ptr=None, stack=None):
        self.message = message

def validVariableName(s):
    if not s[0] in VALID_VARIABLE_START:
        return False
        
    for c in s[1:]:
        if not c in VALID_VARIABLE:
            return False
    return True

def validNameStart(c):
    if c in VALID_VARIABLE_START:
        return True
    return False

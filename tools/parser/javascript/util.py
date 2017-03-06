from .constants import *
from .. import util

ParseError = util.ParseError

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

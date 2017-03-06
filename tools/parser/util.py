class ParseError(Exception):
    def __init__(self, message, parser):
        self.message = message
        self.ptr = parser.ptr
        self.stack = parser.stack
        #print(message, parser.ptr, parser.stack)

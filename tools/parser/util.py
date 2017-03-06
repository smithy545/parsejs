class ParseError(Exception):
    def __init__(self, message, parser):
        self.message = message
        #print(message, parser.ptr, parser.stack)

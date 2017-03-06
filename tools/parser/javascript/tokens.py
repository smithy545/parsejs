from .constants import *
from .util import *

class Token(object):
    """
    Class for storing location information
    about certain found characters
    """

    def __init__(self, line, charPos):
        self.line = line
        self.charPos = charPos

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '(Line: ' + str(self.line) + ', Col: ' + str(self.charPos) + ')'


class Pointer(Token):
    """
    Class for storing location information
    of current character    
    """

    def __init__(self, raw):
        self.index = -1
        self.line = 1
        self.charPos = 0
        self.maxIndex = len(raw)-1
        self.raw = raw

    def next(self):
        self.index += 1
        if self.index == self.maxIndex + 1:
            return None
        if self.index > self.maxIndex + 1:
            raise Exception('Beyond file end')
        self.charPos += 1
        if self.raw[self.index] == '\n':
            self.charPos = 0
            self.line += 1
        return self.raw[self.index]

    def previous(self):
        self.index -= 1
        if self.index < 0:
            raise Exception('Cannot backtrack from start')
        self.charPos -= 1
        if self.raw[self.index + 1] == '\n':
            self.charPos = len(self.raw[self.raw.rfind('\n', 0, self.index):self.index])
            self.line -= 1
        return self.raw[self.index]

    def peek(self, distance=1):
        peekIndex = self.index + distance + 1
        if peekIndex <= self.maxIndex:
            return self.raw[self.index+1:peekIndex]

    def until(self, delim, after=True):
        if after:
            self.next()
        text = ''
        if isinstance(delim, list) or isinstance(delim, set):
            delims = list(delim)
            delims.sort(key=lambda s: len(s))
            delims.reverse()
            maxLen = max([len(delim) for delim in delims])
            while self.index <= self.maxIndex - maxLen:
                for delim in delims:
                    delimLen = len(delim)
                    if self.raw[self.index:self.index + delimLen] == delim:
                        self.skip(delimLen - 1)
                        return text

                text += self.raw[self.index]
                self.next()

        elif isinstance(delim, str):
            delimLen = len(delim)
            while self.index <= self.maxIndex - delimLen:
                if self.raw[self.index:self.index + delimLen] == delim:
                    self.skip(delimLen - 1)
                    return text
                text += self.raw[self.index]
                self.next()

        else:
            raise Exception('Until delimiter must be list or string')

    def untilNot(self, delim, after=True):
        if after:
            self.next()
        text = ''
        if isinstance(delim, list) or isinstance(delim, set):
            delims = list(delim)
            delims.sort(key=lambda s: len(s))
            delims.reverse()
            maxLen = max([len(delim) for delim in delims])
            while self.index <= self.maxIndex - maxLen:
                found = False
                for delim in delims:
                    delimLen = len(delim)
                    if self.raw[self.index:self.index + delimLen] == delim:
                        found = True
                        break

                if not found:
                    return text
                text += self.raw[self.index]
                self.next()

        elif isinstance(delim, str):
            delimLen = len(delim)
            while self.index <= self.maxIndex - delimLen:
                if self.raw[self.index:self.index + delimLen] != delim:
                    return text
                text += self.raw[self.index]
                self.next()

        else:
            raise Exception('Until delimiter must be list or string')

    def seek(self, index):
        if index < 0:
            raise IndexError("Out of bounds: index cannot be less than 0")
        elif index > self.maxIndex:
            raise IndexError("Out of bounds: index greater than max index")

        while self.index > index:
            self.previous()

        while self.index < index:
            self.next()

    def skip(self, distance):
        if distance < 0:
            for i in range(-distance):
                self.previous() 

        else:
            for i in range(distance):
                self.next()

    def whitespace(self, after=False, newline=True):
        if newline:
            check = WHITESPACE
        else:
            check = WHITESPACE.difference(['\n'])
        if not after and self.raw[self.index] not in check:
            return
        while self.next() in check:
            pass

    def current(self):
        if self.index > self.maxIndex:
            raise IndexError('Index out of range')
        return self.raw[self.index]

    def createToken(self):
        return Token(self.line, self.charPos)

    def checkKeyword(self):
        distanceToEnd = self.maxIndex - self.index
        i = self.index
        for length in range(2, 13):
            if distanceToEnd >= length and self.raw[i:i + length] in KEYWORDS[length - 2] and self.raw[i + length] not in VALID_VARIABLE:
                return self.raw[i:i + length]

    def check(self, delims):
        distanceToEnd = self.maxIndex - self.index
        i = self.index
        ops = list(delims)
        ops.sort(key=lambda s: len(s))
        ops.reverse() # search by length starting with longest
        for op in ops:
            length = len(op)
            if distanceToEnd >= length and self.raw[i:i + length] == op:
                return self.raw[i:i + length]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "('" + self.raw[self.index] + "', Line: " + str(self.line) + ', Col: ' + str(self.charPos) + ')'

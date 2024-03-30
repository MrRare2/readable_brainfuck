# -*- coding: utf-8 -*-
""" RBF - Readable Brainfuck

This is RBF, a Brainfuck-inspired esoteric programming language that is more readable than Brainfuck

2024 (c) MrRare (GPLv3 License)
"""
import string
import sys
from time import sleep
from readchar import readchar
from warnings import warn

alphabet = string.ascii_letters
digits = string.digits
CELL_SIZE = 2 ** 16

TT_R = "R"
TT_L = "L"
TT_DEL = "DEL"
TT_SET = "SET"
TT_INPUT = "INPUT"
TT_PRNT = "PRNT"
TT_PRNTN = "PRNTN"
TT_EXIT = "EOF"
TT_INT = "INT"
TT_PMARK = "PMARK"
TT_GOTO = "GOTO"
TT_NEWLINE = "NEWLINE"

KEYWORDS = {
    "SET": TT_SET,
    "CLS": TT_DEL,
    "PRNT": TT_PRNT,
    "PRNTN": TT_PRNTN,
    "EXIT": TT_EXIT,
    "MOVR": TT_R,
    "MOVL": TT_L,
    "GOTO": TT_GOTO,
    "INPUT": TT_INPUT,
}

class Token:
    def __init__(self, tok_type, val=None):
        self.type = tok_type
        self.val = val

    def __repr__(self):
        return f'{self.type}{f":{self.val}" if self.val else ""}'

class Lexer:
    def __init__(self, code):
        self.source = code
        self.pos = 0
        self.char = self.source[self.pos]
        self.tokens = []

    def advance(self):
        self.pos += 1
        if self.pos < len(self.source):
            self.char = self.source[self.pos]
        else:
            self.char = None

    def make(self):
        while self.pos <= len(self.source) and self.char != None:
            if self.char in alphabet:
                tok = self.make_command()
                if tok:
                    self.tokens.append(tok)
            elif self.char in digits:
                tok = self.make_number()
                if tok:
                    self.tokens.append(tok)
            elif self.char in [';', '\n']:
                self.tokens.append(Token(TT_NEWLINE))
                self.advance()
            elif self.char == "!":
                tok = self.make_number_with_pmark()
                if tok:
                    self.tokens.append(tok)
            elif self.char == ' ':
                self.advance()
            elif self.char == "#":
                self.comment()
            else:
                self.advance()

        self.tokens.append(Token(TT_EXIT))
        return self.tokens

    def comment(self):
        self.advance()

        while self.char not in ["\n", "#"]:
            self.advance()
        self.advance()

    def make_command(self):
        main = ''
        while self.char not in [' ', ';', '\n', '\t', '#'] and self.char != None:
            main += self.char.upper()
            self.advance()

        if main in KEYWORDS:
            tok_type = KEYWORDS[main]
        else:
            return None
        
        return Token(tok_type)

    def make_number_with_pmark(self):
      if self.char != "!":
        return None
      self.advance()

      main = ''
      while self.char is not None and self.char in digits:
        main += self.char
        self.advance()

      self.advance()

      if main:
          return Token(TT_PMARK, int(main))
      return None

    def make_number(self):
        main = ''
        while self.char != None and self.char in digits:
            main += self.char
            self.advance()

        self.advance()
        if main:
            return Token(TT_INT, int(main))
        return None

class Parser:
    def __init__(self, tokens):
        self.list = [0 for a in range(CELL_SIZE)]
        self.pointer = 0
        self.current_value = self.list[self.pointer]
        # for token
        self.tokens = tokens
        self.pointer_tok = 0
        self.tok = self.tokens[self.pointer_tok]

    def move_right(self):
        self.pointer += 1
        self.pointer = self.pointer % CELL_SIZE
        self.current_value = self.list[self.pointer]

    def move_left(self):
        self.pointer -= 1
        self.pointer = self.pointer % CELL_SIZE
        self.current_value = self.list[self.pointer]

    def set(self, value, pointer=None):
        point = pointer or self.pointer
        self.list[point % CELL_SIZE] = value 
        self.current_value = self.list[point % CELL_SIZE]
    
    def reset(self, point):
        self.list[point % CELL_SIZE] = 0
        self.current_value = self.list[self.pointer % CELL_SIZE]

    def advance_tok(self):
        self.pointer_tok += 1
        try: self.tok = self.tokens[self.pointer_tok]
        except IndexError: self.tok = None

    def peek_tok(self, count=1):
        try:
            return self.tokens[self.pointer_tok + count]
        except IndexError:
            raise IndexError(
                    "Error while parsing"
            ) from None

    def prnt(self):
        nxt = self.peek_tok()
        if nxt.type == TT_PMARK:
            value = self.find_value(nxt.val)
            print(chr(value % 0x10ffff), end="")
        else:
            print(chr(self.current_value % 0x10ffff), end="")
    
    def prntn(self):
        nxt = self.peek_tok()
        if nxt.type == TT_PMARK:
            value = self.find_value(nxt.val)
            print(value, end="")
        else:
            print(self.current_value, end="")

    def find_value(self, pointer):
        return self.list[pointer % CELL_SIZE]

    def goto(self):
        nxt = self.peek_tok()
        if nxt.type != TT_INT and nxt.type != TT_PMARK:
            nxt.val = 0
        pointer = self.find_value(nxt.val) if nxt.type == TT_PMARK else nxt.val
        self.pointer = pointer
        self.current_value = self.list[self.pointer % CELL_SIZE]
        return

    def parse(self):
        #print(f"debug: Current index is on {self.pointer} out of {CELL_SIZE}")
        while self.tok != None:
            if self.tok.type == TT_SET:
                nxt = self.peek_tok()
                value = nxt.val
                if value:
                    if nxt.type == TT_PMARK:
                        value = self.find_value(nxt.val)
                    self.set(value)
            elif self.tok.type == TT_R:
                self.move_right()
            elif self.tok.type == TT_L:
                self.move_left()
            elif self.tok.type == TT_DEL:
                nxt = self.peek_tok()
                if nxt.val and nxt.type == TT_PMARK:
                    point = nxt.val
                else:
                    point = self.pointer
                self.reset(point)
            elif self.tok.type == TT_PRNT:
                self.prnt()
            elif self.tok.type == TT_PRNTN:
                self.prntn()
            elif self.tok.type == TT_GOTO:
                self.goto()
            elif self.tok.type == TT_INPUT:
                val = readchar()
                nxt = self.peek_tok()
                if nxt.val and nxt.type == TT_PMARK:
                    point = nxt.val
                else:
                    point = None
                self.set(ord(val), pointer=point)
            elif self.tok.type == TT_EXIT:
                exit(0)

            self.advance_tok()
    def compile(self):
        # Don't run if parse() is executed already
        bf = ""
        pos = 0
        tmp = "[-]>[-]<{}[>++++++++++<-]>{}"
        while self.tok != None:
            type = self.tok.type
            if type == TT_SET:
                nxt = self.peek_tok()
                if nxt.type == TT_INT:
                    val = nxt.val % 256
                    tens = "+" * (val // 10)
                    ones = "+" * (val % 10)
                    bf += tmp.format(tens, ones)
                elif nxt.type == TT_PMARK:
                    warn(f"!{nxt.val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
            elif type == TT_R:
                bf += ">"
                pos += 1
            elif type == TT_L:
                bf += "<"
                pos -= 1
            elif type == TT_PRNT:
                if self.peek_tok().type == TT_PMARK:
                    warn(f"!{self.peek_tok().val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
                bf += "."
            elif type == TT_GOTO:
                nxt = self.peek_tok()
                if nxt.type == TT_INT:
                    val = nxt.val
                    far = val - pos
                    if far > 0:
                        bf += ">" * far
                        pos += far
                    elif far < 0:
                        bf += "<" * abs(far)
                        pos -= far
                elif nxt.type == TT_PMARK:
                    warn(f"!{nxt.val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
            elif type == TT_PRNTN:
                warn("prntn has no equivalent command in Brainfuck, this is ignored",UserWarning)
            else:
                pass

            if pos < 0:
                raise IndexError('error: tape memory out of bounds (underrun)\nundershot the tape size of 30000 cells')
            elif pos >= 30_000:
                raise IndexError('error: tape memory out of bounds (overrun)\nexceeded the tape size of 30000 cells')
            self.advance_tok()
        return bf


if __name__ == "__main__":
    compile = False
    if "--compile" in sys.argv:
        compile = True
    if len(sys.argv) > 1 and not compile:
        code = open(sys.argv[1], 'r').read()
        lexer = Lexer(code)
        tokens = lexer.make()
        parser = Parser(tokens)
        parser.parse()
    elif len(sys.argv) > 2 and compile:
        compile_ind = sys.argv.index('--compile')
        code = open(sys.argv[compile_ind + 1 if compile else 1], 'r').read()
        lexer = Lexer(code)
        tokens = lexer.make()
        parser = Parser(tokens)
        bf = parser.compile()
        print("Brainfuck:", bf)
    else:
        try:
            t = sys.stdin.read().strip()
            if not t:
                print("Argument must be two")
            else:
                lexer = Lexer(t)
                tokens = lexer.make()
                parser = Parser(tokens)
                parser.parse() if not compile else print("Brainfuck:", parser.compile())
        except KeyboardInterrupt:
            pass

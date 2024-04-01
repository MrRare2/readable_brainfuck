# -*- coding: utf-8 -*-
""" RBF - Readable Brainfuck

This is RBF, a Brainfuck-inspired esoteric programming language that is more readable than Brainfuck

2024 (c) MrRare (GPLv3 License)
"""
import string
import sys
from time import sleep
from warnings import warn
from typing import Any

alphabet: str = string.ascii_letters
digits: str = string.digits
CELL_SIZE: int = 2 ** 16

# Token types (TT)
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
TT_PLUS = "PLUS"
TT_SUB = "SUB"
TT_SQLEFT = "SQLEFT"
TT_SQRIGHT = "SQRIGHT"
TT_NEWLINE = "NEWLINE"

# Reserved Keywords (to use them in a comment, use # (keyword) # syntax
KEYWORDS: dict[str, str] = {
    "SET": TT_SET,
    "CLS": TT_DEL,
    "PRNT": TT_PRNT,
    "PRNTN": TT_PRNTN,
    "EXIT": TT_EXIT,
    "MOVR": TT_R,
    "MOVL": TT_L,
    "GOTO": TT_GOTO,
    "INPUT": TT_INPUT,
    "WHILE": TT_SQLEFT,
    "END": TT_SQRIGHT,
    "ADD": TT_PLUS,
    "SUB": TT_SUB,
}

class Token:
    def __init__(self, tok_type, val=None):
        self.type = tok_type
        self.val = val

    def __repr__(self):
        return f'{self.type}{f":{self.val}" if self.val else ""}'

class Lexer:
    """Converts source code into parsable tokens"""
    def __init__(self, code: str):
        self.source: str = code
        self.pos: int = 0
        self.char: Any[str, None] = self.source[self.pos]
        self.tokens: list = []

    def advance(self) -> None:
        self.pos += 1
        if self.pos < len(self.source):
            self.char = self.source[self.pos]
        else:
            self.char = None

    def make(self) -> list[Token]:
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
            #elif self.char == "+":
            #    self.tokens.append(Token(TT_PLUS))
            #    self.advance()
            #elif self.char == "-":
            #    self.tokens.append(Token(TT_SUB))
            #    self.advance()
            else:
                self.advance()

        self.tokens.append(Token(TT_EXIT))
        return self.tokens

    def comment(self) -> None:
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
    """ Parse tokens, or compile it into Brainfuck """
    def __init__(self, tokens: list[Token]):
        self.list: list[int] = [0 for a in range(CELL_SIZE)]
        self.pointer: int = 0
        self.current_value: int = self.list[self.pointer]
        # for token
        self.tokens: list[Token] = tokens
        self.pointer_tok: int = 0
        self.tok: Any[Token, None] = self.tokens[self.pointer_tok]
        # call limit (since we have while loops now)
        self.recursion: int = 0
        self.limit: int = 65_536

    def move_right(self) -> None:
        self.pointer += 1
        self.pointer = self.pointer % CELL_SIZE
        self.current_value = self.list[self.pointer]

    def move_left(self) -> None:
        self.pointer -= 1
        self.pointer = self.pointer % CELL_SIZE
        self.current_value = self.list[self.pointer]

    def set(self, value, pointer=None) -> None:
        point = pointer if pointer else self.pointer
        self.list[point % CELL_SIZE] = value 
        self.current_value = self.list[point % CELL_SIZE]
    
    def reset(self, point) -> None:
        self.list[point % CELL_SIZE] = 0
        self.current_value = self.list[point % CELL_SIZE]

    def advance_tok(self) -> None:
        self.recursion += 1
        self.pointer_tok += 1
        try: self.tok = self.tokens[self.pointer_tok]
        except IndexError: self.tok = None

    def peek_tok(self, count=1, no_current=False) -> Token:
        try:
            if not no_current:
                return self.tokens[self.pointer_tok + count]
            else:
                return self.tokens[count]
        except IndexError:
            raise IndexError(
                    "Error while parsing"
            ) from None

    def prnt(self) -> None:
        nxt = self.peek_tok()
        if nxt.type == TT_PMARK:
            value = self.find_value(nxt.val)
            print(chr(value % 0x10ffff), end="")
        else:
            print(chr(self.current_value % 0x10ffff), end="")
    
    def prntn(self) -> None:
        nxt = self.peek_tok()
        if nxt.type == TT_PMARK:
            value = self.find_value(nxt.val)
            print(value, end="")
        else:
            print(self.current_value, end="")

    def find_value(self, pointer) -> int:
        return self.list[pointer % CELL_SIZE]

    def goto(self) -> None:
        nxt = self.peek_tok()
        if nxt.type != TT_INT and nxt.type != TT_PMARK:
            nxt.val = 0
        pointer = self.find_value(nxt.val) if nxt.type == TT_PMARK else nxt.val
        self.pointer = pointer
        self.current_value = self.list[self.pointer % CELL_SIZE]
        return

    def precomp_jump(self) -> dict[int, int]:
        stack: list = []
        ret: dict = {}
        pl: int = 0
        while not pl >= len(self.tokens):
            tok = self.peek_tok(pl, True)
            if tok.type == TT_SQLEFT:
                stack.append(pl)
            elif tok.type == TT_SQRIGHT:
                try:
                    target = stack.pop()
                    ret[target] = pl
                    ret[pl] = target
                except IndexError:
                    pass
            pl += 1
        return ret

    def parse(self) -> None:
        #print(f"debug: Current index is on {self.pointer} out of {CELL_SIZE}")
        jump_map: dict[int, int] = self.precomp_jump()
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
                tty = sys.stdin.isatty()
                if not tty:
                    warn("Your stdin is not a tty, input features may break", UserWarning)
                val = sys.stdin.read(1)
                nxt = self.peek_tok()
                if nxt.val and nxt.type == TT_PMARK:
                    point = nxt.val
                else:
                    point = None
                self.set(ord(val), pointer=point)
            elif self.tok.type == TT_PLUS:
                nxt = self.peek_tok()
                point = self.pointer
                if nxt.val and nxt.type == TT_PMARK:
                    self.set(self.find_value(nxt.val)+1, nxt.val)
                else:
                    self.set(self.find_value(self.pointer)+1)
            elif self.tok.type == TT_SUB:
                nxt = self.peek_tok()
                point = self.pointer
                if nxt.val and nxt.type == TT_PMARK:
                    self.set(self.find_value(nxt.val)-1, nxt.val)
                else:
                    self.set(self.find_value(self.pointer)-1)
            elif self.tok.type == TT_SQLEFT:
                if self.current_value == 0:
                    try:
                        self.pointer_tok = jump_map[self.pointer_tok]
                        self.tok = self.tokens[self.pointer_tok]
                    except KeyError: # when you parse it without TT_SQRIGHT
                        pass
            elif self.tok.type == TT_SQRIGHT:
                if self.current_value != 0:
                    self.pointer_tok = jump_map[self.pointer_tok]
                    self.tok = self.tokens[self.pointer_tok]
            elif self.tok.type == TT_EXIT:
                exit(0)
            if self.recursion >= self.limit:
                warn(f"You hit the recursion limit of {self.limit}.", UserWarning)
                break
            self.advance_tok()
    def compile(self) -> str:
        # Don't run if parse() is executed already
        bf: str = ""
        pos: int = 0
        while self.tok != None:
            type = self.tok.type
            if type == TT_SET:
                nxt = self.peek_tok()
                if nxt.type == TT_INT:
                    bf += "[-]" + ("+" * (nxt.val % 256))
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
                        pos -= abs(far)
                elif nxt.type == TT_PMARK:
                    warn(f"!{nxt.val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
            elif type == TT_PRNTN:
                warn("prntn has no equivalent command in Brainfuck, this is ignored",UserWarning)
            elif type == TT_DEL:
                if self.peek_tok().type == TT_PMARK:
                    warn(f"!{self.peek_tok().val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
                bf += "[-]"
            elif type == TT_INPUT:
                if self.peek_tok().type == TT_PMARK:
                    warn(f"!{self.peek_tok().val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
                bf += ","
            elif type == TT_PLUS:
                if self.peek_tok().type == TT_PMARK:
                    warn(f"!{self.peek_tok().val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
                bf += "+"
            elif type == TT_SUB:
                if self.peek_tok().type == TT_PMARK:
                    warn(f"!{self.peek_tok().val} has no equivalent command in Brainfuck, this is ignored",UserWarning)
                bf += "-"
            elif type == TT_SQLEFT:
                bf += "["
            elif type == TT_SQRIGHT:
                bf += "]"
            else:
                pass

            if pos < 0:
                raise IndexError('error: tape memory out of bounds (underrun)\nundershot the tape size of 30000 cells')
            elif pos >= 30_000:
                raise IndexError('error: tape memory out of bounds (overrun)\nexceeded the tape size of 30000 cells')
            self.advance_tok()
        return bf


if __name__ == "__main__":
    is_compile: bool = False
    if "--compile" in sys.argv:
        is_compile = True
    if len(sys.argv) > 1 and not is_compile:
        code: str = open(sys.argv[1], 'r').read()
        lexer: Lexer = Lexer(code)
        tokens: list[Token] = lexer.make()
        parser: Parser = Parser(tokens)
        parser.parse()
    elif len(sys.argv) > 2 and is_compile:
        compile_ind: int = sys.argv.index('--compile')
        code: str = open(sys.argv[compile_ind + 1 if is_compile else 1], 'r').read()
        lexer: Lexer = Lexer(code)
        tokens: list[Token] = lexer.make()
        parser: Parser = Parser(tokens)
        bf: str = parser.compile()
        print("Brainfuck:", bf)
    else:
        try:
            t: str = sys.stdin.read().strip()
            if not t:
                print("Argument must be two")
            else:
                lexer: Lexer = Lexer(t)
                tokens: list[Token] = lexer.make()
                parser: Parser = Parser(tokens)
                parser.parse() if not is_compile else print("Brainfuck:", parser.compile())
        except KeyboardInterrupt:
            pass

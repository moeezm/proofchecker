import re

def tokenize(s):
    sl = s.split('\n')
    # tag with line numbers
    sl = [(sl[i].strip(), i+1) for i in range(len(sl))]
    # remove comments
    sl = filter(lambda x : len(x) < 2 or x[0][:2] != "//", sl) 
    # split into alphanumeric and nonalphanumeric where the latter
    # are individual chars
    pattern = re.compile(r'[A-Za-z0-9]+|[^A-Za-z0-9]')
    sl = map(lambda x: (pattern.findall(x[0]), x[1]), sl)

    # remove whitespace
    return [("".join(token.split()), x[1]) for x in sl for token in x[0] if len(token.split()) > 0]

# every thing in the grammar returns its type
# except vars just return their name
# types will be represented as binary trees

class Type:
    def __init__(self, val, left, right):
        # val is either an atom or a connective
        # right and left are Type | None
        self.val = val
        self.left = left
        self.right = right
    def __repr__(self):
        if self.left is not None and self.right is not None:
            if self.val == IMPL and self.right.val == "0":
                return f"~{self.left.__repr__()}"
            return f"({self.left.__repr__()} {self.val} {self.right.__repr__()})"
        else:
            return self.val

def typeeq(t1, t2):
    if t1 is None and t2 is None:
        return True
    elif t1 is None or t2 is None:
        return False
    elif t1.val == t2.val:
        return typeeq(t1.left, t2.left) and typeeq(t1.right, t2.right)
    else:
        return False

TRUE = Type("1", None, None)
FALSE = Type("0", None, None)
AND = "&"
OR = "+"
IMPL = ">"
NOT = "~"


class Parser:
    def __init__(self, tokens):
        self.inp = tokens 
        self.pos = 0
        self.N = len(tokens)
        self.line = 0
        # vars is stack of dicts var -> Type to handle scope
        self.vars = [{}]
    
    def expect(self, want):
        c, line = self.peek()
        if c != want:
            raise SyntaxError(f"Expected {want} on line {line}, got {c}")
        self.consume()

    def getvar(self, x):
        res = None
        for frame in self.vars:
            if x in frame:
                res = frame[x]
        return res

    def setvar(self, x, t):
        self.vars[-1][x] = t
        
    def peek(self):
        if self.pos < self.N:
            self.line = self.inp[self.pos][1]
            return self.inp[self.pos]
        else:
            return None, 0
    
    def consume(self):
        c = self.peek()
        if c is not None:
            self.pos += 1
        return c
    
    def program(self, silent=False):
        t = TRUE
        while (res := self.expr(True)) != None:
            t = res
        return t
    
    def expr(self, silent=False):
        c, _ = self.peek()
        if c is None:
            return None
        if c == '(':
            # function
            self.consume()
            var = self.var()
            # push new scope
            self.vars.append({})
            self.expect(":")
            inptype = self.type()
            self.setvar(var, inptype)
            self.expect(',')
            outtype = self.type()

            self.expect(')')
            self.expect('{')

            ptype = self.program()
            if not typeeq(outtype, ptype):
                raise TypeError(f"Function is expected to output {outtype} but outputs {ptype} instead")
            # remove scope
            self.vars.pop()
            self.expect('}')
            return Type(IMPL, inptype, outtype)
        elif c == '<':
            # product
            self.consume()
            expr1 = self.expr()
            self.expect(",")
            expr2 = self.expr()
            self.expect(">")
            return Type(AND, expr1, expr2)
        elif c == "p1":
            # projection 1
            self.consume()
            self.expect('(')
            expr1 = self.expr()
            if expr1.val != AND:
                raise TypeError(f"Expected conjunction expression on line {self.line}")
            self.expect(")")
            return expr1.left 
        elif c == "p2":
            # projection 2
            self.consume()
            self.expect('(')
            expr1 = self.expr()
            if expr1.val != AND:
                raise TypeError(f"Expected conjunction expression on line {self.line}")
            self.expect(")")
            return expr1.right
        elif c == "cons":
            # disjunction construct
            self.consume()
            self.expect('(')
            t1 = self.type()
            self.expect(",")
            t2 = self.type()
            self.expect(",")
            expr1 = self.expr()
            if not (typeeq(expr1, t1) or typeeq(expr1, t2)):
                raise TypeError(f"Need expression to be one of types in disjunction on line {self.line}")
            self.expect(")")
            return Type(OR, t1, t2)
        elif c == "case":
            # disjunction elimination
            self.consume()
            self.expect('(')
            evalexpr = self.expr()
            if evalexpr.val != OR:
                raise TypeError(f"Need disjunction type for case on line {self.line}")
            self.expect(',')
            expr1 = self.expr()
            if expr1.val != IMPL:
                raise TypeError(f"Need branch of case to be implication on line {self.line}")
            if not typeeq(expr1.left, evalexpr):
                raise TypeError(f"Need input to case branch same type as branching expr on line {self.line}")
            self.expect(',')
            expr2 = self.expr()
            if expr2.val != IMPL:
                raise TypeError(f"Need branch of case to be implication on line {self.line}")
            if not typeeq(expr2.left, evalexpr):
                raise TypeError(f"Need input to case branch same type as branching expr on line {self.line}")

            if not typeeq(expr1.right, expr2.right):
                raise TypeError(f"Need output of both branches of case to be the same on line {self.line}")

            self.expect(')')
            return expr1.right
        elif c == "explode":
            # principle of explosion
            self.consume()
            self.expect('(')
            expr1 = self.expr()
            if not typeeq(expr1, FALSE):
                raise TypeError(f"Need false statement to use explode")
            self.expect(',')
            type1 = self.type()
            self.expect(")")
            return type1
        elif (var := self.var(True)) is not None:
            c, _ = self.peek()
            if c == '=':
                # assignment
                self.consume()
                expr1 = self.expr()
                self.setvar(var, expr1)
                return expr1
            
            # var already exists
            varT = self.getvar(var)
            if varT is None:
                raise TypeError(f"Variable {var} doesn't exist on line {self.line}")
            if c == "(":
                # function application
                self.consume()
                if varT.val != IMPL:
                    raise TypeError(f"Variable {var} is not an implication on line {self.line}")
                expr1 = self.expr()
                if not typeeq(varT.left, expr1):
                    raise TypeError(f"Variable {var} input type doesn't match on line {self.line}")
                self.expect(")")
                return varT.right
            # lone variable
            return varT
        else:
            if silent:
                return None
            else:
                raise SyntaxError(f"Expected expression on line {self.line}")
    
    def var(self, silent=False):
        c, line  = self.peek()
        if not c.isalpha():
            if silent: return None
            else: raise SyntaxError(f"Variable names must be alphabetical (line {line}): {c}")
        self.consume()
        return c

    def type(self, silent=False):
        c, _ = self.peek()
        if (s1 := self.sub(True)) is not None:
            c, _ = self.peek()
            if c in [IMPL, AND, OR]:
                self.consume()
                s2 = self.sub()
                return Type(c, s1, s2)
            else:
                return s1
        else:
            if silent: return None
            else: raise SyntaxError(f"Expected a type on line {self.line}")
    
    def sub(self, silent=False):
        c, _ = self.peek()
        if c == NOT:
            self.consume()
            s1 = self.sub()
            return Type(IMPL, s1, FALSE)
        elif c == '(':
            self.consume()
            t1 = self.type()
            self.expect(')')
            return t1
        elif (a := self.atom(True)) is not None:
            return a
        else:
            if silent: return None
            else: raise SyntaxError(f"Expected a logical expression on line {self.line}, got {self.peek()[0]}")

    def atom(self, silent=False):
        c, _ = self.peek()
        if c.isalpha() or c in ["1", "0"]:
            self.consume()
            return Type(c, None, None)
        else:
            if silent: return None
            else: raise SyntaxError(f"Expected atom (alphabetic string or boolean 0/1) on line {self.line}")

if __name__ == "__main__":
    with open("example.nd", "r") as f:
        s = f.read()
        tokens = tokenize(s)
        # print(*tokens)
        p = Parser(tokens)
        print(p.program())
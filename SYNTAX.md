// example syntax

// implication / function
// A is input type, y is placeholder name for input of type A, type B is output type
x = (y : A, B) {
	...
}
x(y)

// conjunction / product type
x = <y, z> // type inferred
a = p1(y)
b = p2(x)
// x = <p1(x), p2(x)>

// disjunction / sum type
x = cons(TYPE1, TYPE2, a) // if a is of type TYPE1 or of type TYPE2, x is now type TYPE1 + TYPE2
x = case(w, y, z) // where w is a disjunction type A + B, y is an function A => C, z is a function B => C, then x is type C

// special symbols 1 and 0 for true and false (unit and empty types)

// just in case my system is not sound 
x = explode(y, A) // if y is type 0 then x is type A

a program's type is just the type of its last expression

note: curried functions are kinda rough rn b/c you
can't do something like f(a)(b) since a function has
to be a variable, can't be an expression, i think
that would make the grammar more complicated

Grammar
=======
// ~A is shorthand for A => 0
Type : Atom | (Type) > (Type) | (Type) & (Type) | (Type) + (Type) | ~(Type)
Atom : alphabetic string | 1 | 0

Program : Expr | Expr Program
Expr : Var | Var = Expr | (Var : Type, Type) {Program} | <Expr, Expr> | p1(Expr) | p2(Expr) | cons(Type, Type, Expr) | case(Expr, Expr, Expr) | explode(Expr, Type) | Var(Expr)
Var : alphabetic string

Type : Sub | Sub > Sub | Sub & Sub | Sub + Sub | Sub
Sub : Atom | (Type) | ~Sub
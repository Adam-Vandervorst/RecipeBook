import os
from collections import Counter
from time import monotonic_ns, time
from glob import glob

from hyperon import MeTTa, interpret, S, SymbolAtom, VariableAtom, ExpressionAtom, GroundedAtom, OperationAtom, AtomType


def color(t, c):
    cmap = [90, 91, 31, 93, 92, 32, 36, 96, 94, 34, 35, 95, 38]
    return f"\033[{cmap[c % len(cmap)]}m{t}\033[0m"


def oblique(t):
    return f"\033[3m{t}\033[0m"


def underline(t):
    return f"\033[4m{t}\033[0m"


def expr_vars(expr):
    if isinstance(expr, SymbolAtom):
        return []
    elif isinstance(expr, VariableAtom):
        return [str(expr)]
    elif isinstance(expr, ExpressionAtom):
        return [e for c in expr.get_children() for e in expr_vars(c)]
    elif isinstance(expr, GroundedAtom):
        return []
    else:
        raise Exception("Unexpected sexpr type: " + str(type(expr)))


def color_expr(expr, level=0, unif_vars=None):
    name = str(expr)
    if level == 0:
        unif_vars = frozenset(e for e, c in Counter(expr_vars(expr)).items() if c > 1) \
            if unif_vars is None else frozenset()
    if isinstance(expr, SymbolAtom):
        return name
    elif isinstance(expr, VariableAtom):
        return oblique(name) if name in unif_vars else name
    elif isinstance(expr, ExpressionAtom):
        return (color("(", level) +
                " ".join(color_expr(c, level + 1, unif_vars) for c in expr.get_children()) +
                color(")", level))
    elif isinstance(expr, GroundedAtom):
        return underline(name)
    else:
        raise Exception("Unexpected sexpr type: " + str(type(expr)))


class ExtendedMeTTa(MeTTa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_atom("transform", OperationAtom("transform", lambda pattern, template: self.space().subst(pattern, template),
                                                      type_names=[AtomType.ATOM, AtomType.ATOM, AtomType.UNDEFINED], unwrap=False))
        self.register_atom("join", OperationAtom("join", lambda a, b: interpret(self.space(), a) + interpret(self.space(), b),
                                                 type_names=[AtomType.ATOM, AtomType.ATOM, AtomType.ATOM], unwrap=False))


class LazyMeTTa(ExtendedMeTTa):
    def lazy_import_file(self, fname):
        path = fname.split(os.sep)
        with open(os.sep.join(self.cwd + path), "r") as f:
            program = f.read()
        self.lazy_run(self._parse_all(program))

    def lazy_run(self, stream):
        for i, (expr, result_set) in enumerate(self.lazy_run_loop(stream)):
            if result_set:
                print(f"> {color_expr(expr)}")
                for result in result_set:
                    print(color_expr(result))
            else:
                print(f"> {color_expr(expr)} /")

    def lazy_run_loop(self, stream):
        interpreting = False
        commented = False
        for expr in stream:
            if expr == S('!') and not commented:
                interpreting = True
            elif expr == S('/*'):
                commented = True
            elif expr == S('*/'):
                commented = False
            elif interpreting and not commented:
                yield expr, interpret(self.space(), expr)
                interpreting = False
            elif not commented:
                self.space().add_atom(expr)


class InteractiveMeTTa(LazyMeTTa):
    def repl_loop(self):
        history = []

        while True:
            line = input()
            if not line:
                continue
            history.append(line + '\n')
            prefix = line[0]
            rest = line[1:].strip()

            if prefix == ";":
                continue
            elif prefix == "s":
                name = f"session_{round(time())}.mettar" if rest == "" else (
                    rest if rest.endswith("mettar") else rest + ".mettar")
                with open(os.sep.join(self.cwd + name), 'w') as f:
                    f.writelines(history)
                continue
            elif prefix == "l":
                name = max(glob("session_*.mettar")) if rest == "" else (
                    rest if rest.endswith("mettar") else rest + ".mettar")
                self.lazy_import_file(name)
                continue
            elif prefix == "q":
                break

            expr = self.parse_single(rest)

            if prefix == "!":
                yield expr, interpret(self.space(), expr)
            elif prefix == "?":
                yield expr, self.space().subst(expr, expr)
            elif prefix == "+":
                self.space().add_atom(expr)
            elif prefix == "-":
                self.space().remove_atom(expr)
            else:
                print(f"prefix {prefix} not recognized, start a query with !, ?, +, or -")

    def repl(self):
        for i, (expr, result_set) in enumerate(self.repl_loop()):
            if result_set:
                for result in result_set:
                    print(color_expr(result))
            else:
                print(f"/")


if __name__ == "__main__":
    os.system('clear')
    print(underline("Recipe Book\n"))
    metta = InteractiveMeTTa()
    metta.cwd = ["recipebook"]
    t0 = monotonic_ns()
    metta.lazy_import_file("study_group_example.metta")
    print(f"\nloading took {(monotonic_ns() - t0)/1e9:.5} seconds, repl:")
    metta.repl()

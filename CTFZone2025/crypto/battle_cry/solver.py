
# solve_battle_cry_z3_fixed.py
# Usage: pip install z3-solver && python solve_battle_cry_z3_fixed.py
import json, re, inspect, importlib.util, sys
from pathlib import Path
from functools import reduce
from z3 import Solver, Bool, Xor, And, Or, Not, sat, BoolVal, simplify

here = Path(__file__).resolve().parent
task_py = here / "battle_cry" / "task.py"
gamma_json = here / "battle_cry" / "gamma.json"

spec = importlib.util.spec_from_file_location("task", str(task_py))
task = importlib.util.module_from_spec(spec)
sys.modules["task"] = task
spec.loader.exec_module(task)

gamma = json.loads(gamma_json.read_text())

# Extract taps from lfsrN
def taps_from_function(func):
    src = inspect.getsource(func)
    ret = src.split("return",1)[1]
    xs = set(int(m.group(1)) for m in re.finditer(r'\bx(\d+)\b', ret))
    return sorted(xs)

taps = [
    taps_from_function(task.lfsr1),
    taps_from_function(task.lfsr2),
    taps_from_function(task.lfsr3),
    taps_from_function(task.lfsr4),
    taps_from_function(task.lfsr5),
    taps_from_function(task.lfsr6),
]
lengths = [5,7,9,11,13,19]

# Build F as z3 boolean by parsing the return expression:
# Map: integer 0/1 -> False/True; ^ -> XOR; * -> AND; variables x1..x6 -> Bool symbols passed in.
F_src = inspect.getsource(task.F)
body = F_src.split("return", 1)[1].strip()
# Cut trailing comment/whitespace
if '\n' in body:
    body = body.splitlines()[0]
# Ensure we only have the expression
if body.endswith(';'):
    body = body[:-1]

def F_bool(x):
    # x is list of 6 BoolRefs
    expr = body
    # normalize spaces
    expr = re.sub(r'\s+', ' ', expr)
    # Replace operators with python-evaluable using z3 Bool ops:
    # We'll convert to a lambda string that uses functions Xor() and And(), plus parentheses.
    # Strategy: split on '^' into XOR terms; each term further split by '*' into AND factors.
    # This preserves operator precedence: * before ^.
    xor_terms = [t.strip() for t in expr.split('^')]
    def parse_and_term(term):
        factors = [f.strip() for f in term.split('*')]
        zf = []
        for f in factors:
            if f == '1':
                zf.append(BoolVal(True))
            elif f == '0':
                zf.append(BoolVal(False))
            elif re.fullmatch(r'x[1-6]', f):
                idx = int(f[1:]) - 1
                zf.append(x[idx])
            else:
                raise ValueError(f"Unexpected token in F: {f}")
        return reduce(lambda a,b: And(a,b), zf) if len(zf) > 1 else zf[0]
    zxor = [parse_and_term(t) for t in xor_terms]
    return reduce(lambda a,b: Xor(a,b), zxor) if len(zxor) > 1 else zxor[0]

# Model
T = min(1024, len(gamma))
s = Solver()

state = []
outs  = []
for i,m in enumerate(lengths):
    state.append([[Bool(f"r{i+1}_t{t}_b{j}") for j in range(m)] for t in range(T+1)])
    outs.append([Bool(f"a{i+1}_t{t}") for t in range(T)])

for i,m in enumerate(lengths):
    tap_idx = taps[i]
    for t in range(T):
        tapped = [ state[i][t][j] for j in tap_idx ]
        outs_expr = reduce(lambda a,b: Xor(a,b), tapped) if len(tapped)>1 else tapped[0]
        s.add( outs[i][t] == outs_expr )
        for j in range(m-1):
            s.add( state[i][t+1][j] == state[i][t][j+1] )
        s.add( state[i][t+1][m-1] == outs[i][t] )

# Combiner constraints
for t in range(T):
    comb = F_bool([outs[i][t] for i in range(6)])
    s.add( comb == BoolVal(bool(gamma[t])) )

# OPTIONAL: forbid trivial all-zero initial state per LFSR (uncomment if needed)
# for i in range(6):
#     s.add( Or(*state[i][0]) )

print("[*] Solving...")
if s.check() != sat:
    print("UNSAT. Try increasing T or re-check files.")
    sys.exit(1)
model = s.model()
print("[+] Model found! Extracting initial states...")
init_states = []
for i,m in enumerate(lengths):
    bits = [ 1 if model.evaluate(state[i][0][j]) is True else 0 for j in range(m) ]
    init_states.append(bits)
    print(f"r{i+1}:", ''.join(map(str,bits)))

# Stream a1..a6 and try to spot CTFZONE{...}
stream_bits = []
for t in range(T):
    vals = [1 if model.evaluate(outs[i][t]) is True else 0 for i in range(6)]
    stream_bits.extend(vals)

def bits_to_bytes(bits, offset):
    bs = []
    cur = 0
    k = 0
    for b in bits[offset:]:
        cur = (cur<<1) | b
        k += 1
        if k == 8:
            bs.append(cur)
            cur = 0
            k = 0
    return bytes(bs)

needle = b"CTFZONE{"
for off in range(8):
    bb = bits_to_bytes(stream_bits, off)
    pos = bb.find(needle)
    if pos != -1:
        tail = bb[pos:pos+256]
        text = tail.decode('latin1', errors='ignore')
        if '}' in text:
            print(f"[+] Flag: {text.split('}',1)[0]+'}'}")
            break

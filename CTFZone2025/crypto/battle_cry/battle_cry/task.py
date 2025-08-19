import json

def lfsr1(x0,x1, x2, x3, x4):
    return x0 ^ x2

def lfsr2(x0,x1, x2, x3, x4, x5, x6):
    return x0 ^ x1

def lfsr3(x0,x1, x2, x3, x4, x5, x6, x7, x8):
    return x0 ^ x4

def lfsr4(x0,x1, x2, x3, x4, x5, x6, x7, x8, x9, x10):
    return x0 ^ x2

def lfsr5(x0,x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12):
    return x0 ^ x1 ^ x3 ^ x4

def lfsr6(x0, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15, x16, x17, x18):
    return x0 ^ x1 ^ x2 ^ x5

def F(x1, x2, x3, x4, x5,x6):
    return 1 ^ x4 ^ x4 * x6 ^ x4 * x5 ^ x4 * x5 * x6 ^ x3 ^ x3 * x6 ^ x3 * x5 * x6 ^ x3 * x4 ^ x3 * x4 * x6 ^ x3 * x4 * x5 * x6 ^ x2 * x6 ^ x2 * x5 ^ x2 * x5 * x6 ^ x2 * x4 ^ x2 * x4 * x6 ^ x2 * x4 * x5 * x6 ^ x2 * x3 * x6 ^ x2 * x3 * x4 ^ x2 * x3 * x4 * x5 ^ x2 * x3 * x4 * x5 * x6 ^ x1 * x6 ^ x1 * x5 ^ x1 * x5 * x6 ^ x1 * x4 ^ x1 * x3 ^ x1 * x3 * x6 ^ x1 * x3 * x5 ^ x1 * x3 * x4 ^ x1 * x3 * x4 * x5 ^ x1 * x2 ^ x1 * x2 * x5 ^ x1 * x2 * x5 * x6 ^ x1 * x2 * x4 * x6 ^ x1 * x2 * x4 * x5 * x6 ^ x1 * x2 * x3 * x6 ^ x1 * x2 * x3 * x5 ^ x1 * x2 * x3 * x5 * x6

"""
[DEBUG INFO]
Linear approximation F: x6 ⊕ 1 (P = 0.625);
Linear approximation F: x5 (P = 0.5625); 
Linear approximation F: x4 (P = 0.59375); 
Linear approximation F: x3 ⊕ 1 (P = 0.59375);
Linear approximation F: x2 ⊕ 1 (P = 0.625);
Linear approximation F: x1 ⊕ 1 (P = 0.59375);
"""


def generate_gamma(length, state_lfsr1, state_lfsr2, state_lfsr3, state_lfsr4, state_lfsr5, state_lfsr6):
    gamma = []
    for _ in range(length):
        a1 = lfsr1(*state_lfsr1)
        a2 = lfsr2(*state_lfsr2)
        a3 = lfsr3(*state_lfsr3)
        a4 = lfsr4(*state_lfsr4)
        a5 = lfsr5(*state_lfsr5)
        a6 = lfsr6(*state_lfsr6)
        gamma.append(F(state_lfsr1[0], state_lfsr2[0], state_lfsr3[0], state_lfsr4[0], state_lfsr5[0], state_lfsr6[0]))
        state_lfsr1 = state_lfsr1[1:] + [a1]
        state_lfsr2 = state_lfsr2[1:] + [a2]
        state_lfsr3 = state_lfsr3[1:] + [a3]
        state_lfsr4 = state_lfsr4[1:] + [a4]
        state_lfsr5 = state_lfsr5[1:] + [a5]
        state_lfsr6 = state_lfsr6[1:] + [a6]
    return gamma


def main():
    start_state_lfsr1 = [0, 0, 0, 0, 0]
    start_state_lfsr2 = [0, 0, 0, 0, 0, 0, 0]
    start_state_lfsr3 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    start_state_lfsr4 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    start_state_lfsr5 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    start_state_lfsr6 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    gamma = generate_gamma(4621, start_state_lfsr1, start_state_lfsr2, start_state_lfsr3, start_state_lfsr4, start_state_lfsr5, start_state_lfsr6)
    with open("gamma.json", "w") as fd:
        json.dump(gamma, fd)

if __name__ == "__main__":
    main()

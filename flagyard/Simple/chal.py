from secrets import randbelow

M = 2**128

def enc(msg, key):
    o = [2, 73]
    for i, p in enumerate(map(ord, msg)):
        o.append(((key*o[i+1])^(key+(o[i]*p))) % M)
    return o

key = randbelow(2**64)
ct = enc(123, key)
print(ct)

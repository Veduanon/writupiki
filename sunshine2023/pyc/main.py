# uncompyle6 version 3.5.0
# Python bytecode 3.8 (3413)
# Decompiled from: Python 2.7.5 (default, Jun 20 2023, 11:36:40) 
# [GCC 4.8.5 20150623 (Red Hat 4.8.5-44)]
# Embedded file name: dill.py
# Size of source mod 2**32: 914 bytes


class Dill:
    prefix = 'sun{'
    suffix = '}'
    o = [5, 1, 3, 4, 7, 2, 6, 0]

    def __init__(self) -> None:
        self.encrypted = 'bGVnbGxpaGVwaWNrdD8Ka2V0ZXRpZGls'

    def validate(self, value: str) -> bool:
        if not (value.startswith(Dill.prefix) and value.endswith(Dill.suffix)):
            return False
        value = value[len(Dill.prefix):-len(Dill.suffix)]
        if len(value) != 32:
            return False
        c = [value[i:i + 4] for i in range(0, len(value), 4)]
        value = ''.join([c[i] for i in Dill.o])
        if value != self.encrypted:
            return False
        else:
            return True
        
if __name__ == '__main__':
    dill = Dill()
    print(dill.validate('sun{kpwe}'))
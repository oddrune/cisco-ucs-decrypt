#!/usr/bin/env python3
# Decrypts strings found in UCS Manager backups

import sys
import base64

key = bytearray.fromhex(
    "0972ad96ac8907accb8e59cc094e72d48824f09cb8b7e6564b04d9cbbcc634e9" +\
    "925f90bb58cc767a6c5fcde8ad8daad29ba112db0383f1f0f199d075fa2b5434" +\
    "2a51c59b22976af23ca0003434a723fdb829cb542e2c527ce3290f4c2f6e9a29" +\
    "f2e4248a653130396f21c0a62c21c6f532498e7c8e124b31")

def decrypt(c):
    out = []
    for i in range(len(c)):
        out.append(chr(c[i] ^ key[i]))
    return "".join(out)

if __name__ == '__main__':
    print(decrypt(base64.b64decode(sys.argv[1])))
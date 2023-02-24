#!/usr/bin/env python3
# Deobfuscates some passwords found in UCS Manager configurations. Use cisco-ucs-decrypt.py first.

import sys

def decrypt(cipher_text, key):
    plain = []
    while len(key)<len(cipher_text):
        key += key # duplicate the key to match cipher length
    for i in range(len(cipher_text)):
        ch = cipher_text[i]
        k = key[i]
        if (ch.isupper()) or (ch.islower()):
            base = ch.islower() and ord('a') or ord('A')
            k = ch.islower() and k.lower() or k.upper()
            p = base + ((ord(ch) - ord(k) + 26) % 26)
            plain.append(chr(p))
        else:
            plain.append(ch) # number, punctuation etc
    return("".join(plain))

if __name__ == "__main__":
    print(decrypt(sys.argv[1], "DWEFSAVFSDKFQWEQYRMFVSFWTH"))
   
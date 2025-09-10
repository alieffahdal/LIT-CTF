import socket
import re
import math
from sympy import factorint

HOST = "litctf.org"
PORT = 31789

def recv_until(s, marker=b"\n"):
    data = b""
    while not data.endswith(marker):
        chunk = s.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode()

def sendline(s, msg):
    s.sendall(msg.encode() + b"\n")

# --- Step 1: Connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# baca sambutan awal
welcome = recv_until(s)
print("[SERVER]", welcome)

# --- Step 2: Kirim modulus (ganti n_guess dengan hasil kamu)
n_guess = 13028753089872053474932529941356876942419261559625474338051059410328470165788918 # <-- isi full hasil kamu

sendline(s, str(n_guess))

reply = recv_until(s)
print("[SERVER after n]", reply)

# --- Step 3: Cek apakah server kasih ciphertext
# biasanya formatnya angka besar / hex / "ciphertext=...."
if "cipher" in reply.lower() or re.search(r"\d{50,}", reply):  
    print("[*] Ciphertext terdeteksi!")

    # coba ekstrak ciphertext
    m = re.search(r"(\d{50,})", reply)
    if m:
        ciphertext = int(m.group(1))
        print("[+] Ciphertext =", ciphertext)

        # Faktorisasi n (gunakan sympy.factorint untuk coba)
        print("[*] Faktorisasi n, ini bisa lama...")
        factors = factorint(n_guess)
        print("[+] factors:", factors)

        # hitung phi(n)
        phi = 1
        for p, k in factors.items():
            phi *= (p-1) * (p**(k-1))

        e = 65537
        d = pow(e, -1, phi)

        # decrypt
        plaintext_int = pow(ciphertext, d, n_guess)
        try:
            plaintext = bytes.fromhex(hex(plaintext_int)[2:]).decode()
        except:
            plaintext = str(plaintext_int)
        print("[+] Plaintext =", plaintext)

        sendline(s, plaintext)
        final_reply = recv_until(s)
        print("[SERVER final]", final_reply)

else:
    print("[*] Sepertinya challenge cuma butuh modulus n")

#!/usr/bin/env python3
import socket
from math import gcd
from functools import reduce
import time

HOST = "litctf.org"
PORT = 31789

# range x yang sesuai server (dari debug sebelumnya)
START = 1000000000
COUNT = 10  # jumlah angka yang dikirim
DBG = True

def recv_until(sock, marker=b": "):
    data = b""
    while not data.endswith(marker):
        chunk = sock.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode()

def query_x(sock, x):
    sock.sendall(f"{x}\n".encode())
    data = sock.recv(4096).decode()
    # ambil hanya digit terpanjang di response
    digits = [d for d in data.split() if d.isdigit()]
    if digits:
        digits.sort(key=len, reverse=True)
        return int(digits[0])
    return None

def compute_gcd(values):
    return reduce(gcd, values)

def main():
    sock = socket.create_connection((HOST, PORT))
    banner = recv_until(sock)
    if DBG:
        print("[SERVER]", banner.strip())

    results = []
    for i in range(COUNT):
        x = START + i
        y = query_x(sock, x)
        if DBG:
            print(f"[DBG] x={x} y={'None' if y is None else len(str(y))} digits")
        if y:
            results.append(y)
        time.sleep(0.05)

    if len(results) < 2:
        print("[!] Tidak cukup hasil, adjust START atau COUNT")
        sock.close()
        return

    # buat kandidat GCD dari perbedaan berturut-turut
    diffs = [results[i] - results[i-1] for i in range(1, len(results))]
    n_guess = compute_gcd(diffs)
    print(f"[+] Candidate modulus n (bitlen={n_guess.bit_length()}):\n{n_guess}")

    # simpan ke file
    with open("modulus.txt", "w") as f:
        f.write(str(n_guess))
    print("[+] Saved modulus to modulus.txt")

    # submit guess
    sock.sendall(b"guess\n")
    prompt = sock.recv(4096)  # server akan tanya "What is n?"
    sock.sendall(f"{n_guess}\n".encode())
    reply = sock.recv(4096).decode()
    print("[SERVER after guess]:\n", reply.strip())

    sock.close()

if __name__ == "__main__":
    main()

import socket
from math import gcd
from functools import reduce

HOST = "litctf.org"   # ganti sesuai challenge
PORT = 31789

def query_server(x):
    s = socket.socket()
    s.connect((HOST, PORT))
    s.recv(4096)  # banner
    s.sendall(f"{x}\n".encode())
    data = s.recv(4096).decode()
    s.close()
    return data.strip()

def compute_gcd(cands):
    return reduce(gcd, cands)

def main():
    start = 10**12   # coba angka besar
    results = []

    for i in range(12):
        x = start + i
        resp = query_server(x)
        print(f"[DBG] x={x} resp={resp[:80]}...")  # print sebagian saja

        if resp.isdigit():
            results.append(int(resp))

    if not results:
        print("Tidak ada kandidat, coba ganti start value")
        return

    diffs = [results[i] - results[i-1] for i in range(1, len(results))]
    n_guess = compute_gcd(diffs)

    print(f"\n[+] Candidate modulus n (bitlen={n_guess.bit_length()}):")
    print(n_guess)

    # Simpan ke file
    with open("modulus.txt", "w") as f:
        f.write(str(n_guess))

    print("[+] Saved full modulus to modulus.txt")

if __name__ == "__main__":
    main()

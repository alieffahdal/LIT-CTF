import socket
import math
from functools import reduce

HOST = "litctf.org"
PORT = 31789

def query_x(x):
    s = socket.socket()
    s.connect((HOST, PORT))
    s.recv(4096)  # prompt awal
    s.sendall(str(x).encode() + b"\n")
    resp = s.recv(4096).decode()
    s.close()
    try:
        return int(resp.strip())
    except:
        return None

def gcd_all(values):
    return reduce(math.gcd, values)

def main():
    xs = [10**5, 10**6, 10**7, 10**8, 10**9]  # bisa kamu ubah-ubah kalau mau
    pairs = []
    for x in xs:
        y = query_x(x)
        print(f"x={x} → y={y}")
        pairs.append((x, y))

    candidates = []
    for i in range(len(pairs)):
        for j in range(i+1, len(pairs)):
            x1,y1 = pairs[i]
            x2,y2 = pairs[j]
            if y1 is None or y2 is None: 
                continue
            # hitung perbedaan
            diff = pow(y1, x2) - pow(y2, x1)
            candidates.append(abs(diff))

    if not candidates:
        print("Gagal dapat kandidat n (mungkin x terlalu kecil/besar)")
        return

    n_guess = gcd_all(candidates)
    print("\n=== Kandidat n ===")
    print(n_guess)
    print("Bit length:", n_guess.bit_length())

if __name__ == "__main__":
    main()

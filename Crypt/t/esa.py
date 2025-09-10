#!/usr/bin/env python3
# exploit_socket_auto.py
# Robust socket-only exploit to recover n from server responses.

import socket
import re
import time
from math import gcd
from functools import reduce

HOST = "litctf.org"
PORT = 31789

# minimal x supaya x**2 >= 996491788296388609
MIN_X = 998244353

# Try parameters
START = max(MIN_X, 10**9)   # default start (>= MIN_X)
COUNT = 12                  # how many consecutive x to collect each try
MAX_TRIES = 12              # max times to shift start (avoid infinite loop)
GOOD_BITLEN = 900           # threshold to accept candidate n (1024 expected)

int_re = re.compile(r"\d{10,}")  # match runs of digits (>=10 digits to avoid small numbers)

def recv_until(sock, sep=b": ", timeout=6):
    """Read until separator appears or timeout"""
    sock.settimeout(timeout)
    data = b""
    while True:
        try:
            chunk = sock.recv(1)
            if not chunk:
                break
            data += chunk
            if data.endswith(sep):
                break
        except socket.timeout:
            break
    return data

def recv_all_now(sock, timeout=0.25):
    """Try reading all available data (non-blocking-ish)"""
    sock.settimeout(timeout)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    return data

def query_many(start, count):
    """Connect once and send consecutive x = start .. start+count-1.
       Return list of (x, y_int_or_None, raw_response)."""
    xs = []
    ys = []
    raws = []
    try:
        s = socket.create_connection((HOST, PORT), timeout=8)
    except Exception as e:
        print("[!] connection failed:", e)
        return [], [], []

    # read initial banner until prompt
    banner = recv_until(s, b": ")
    # we will send numbers; server expects a prompt before each send
    for i in range(count):
        x = start + i
        try:
            s.sendall(str(x).encode() + b"\n")
        except Exception as e:
            print("[!] send error:", e)
            break
        # after sending, read one or two lines (server may print result then prompt)
        raw = recv_all_now(s).decode(errors="ignore")
        # sometimes prompt may not come immediately; ensure we capture at least something
        if not raw:
            # wait a little and try again
            time.sleep(0.15)
            raw = recv_all_now(s).decode(errors="ignore")
        # parse largest integer present (likely the pow output)
        matches = int_re.findall(raw)
        y = None
        if matches:
            # choose the longest digit run (most likely the big modulo result)
            matches.sort(key=len, reverse=True)
            try:
                y = int(matches[0])
            except:
                y = None
        # handle "Too small" explicitly
        if "Too small" in raw:
            # server won't consume a "try" counter; we should continue with next x
            y = None
        xs.append(x)
        ys.append(y)
        raws.append(raw.strip())
        print(f"[DBG] x={x} -> {'Too small' if y is None else f'{len(str(y))} digits'}")
    try:
        s.close()
    except:
        pass
    return xs, ys, raws

def compute_candidate_gcd(ys):
    # require at least 3 non-None ys and adjacent values
    # build list of usable consecutive triples' diffs
    vals = []
    # filter contiguous runs of non-None results
    run_idxs = []
    cur = []
    for i,y in enumerate(ys):
        if y is not None:
            cur.append(i)
        else:
            if len(cur) >= 3:
                run_idxs.append(cur)
            cur = []
    if len(cur) >= 3:
        run_idxs.append(cur)
    # For each run, compute triple diffs and pair determinants
    for run in run_idxs:
        n = len(run)
        for k in range(n-2):
            i = run[k]
            j = run[k+1]
            k2 = run[k+2]
            r1 = ys[i]; r2 = ys[j]; r3 = ys[k2]
            d = r2*r2 - r1*r3
            if d != 0:
                vals.append(abs(d))
        # pairwise determinants for more candidates
        for a in range(n-1):
            for b in range(a+1, n):
                i = run[a]
                j = run[b]
                if j+1 >= run[-1]+1:  # ensure j+1 within collected indices
                    # but we only have actual indices; skip if out of range
                    if (j+1) >= len(ys):
                        continue
                # try using i,i+1 and j,j+1 if available
                if (i+1 in run) and (j+1 in run):
                    r_i = ys[i]; r_ip = ys[i+1]
                    r_j = ys[j]; r_jp = ys[j+1]
                    diff = r_i * r_jp - r_ip * r_j
                    if diff != 0:
                        vals.append(abs(diff))
    # filter and gcd
    vals = [v for v in vals if v is not None and v != 0]
    if not vals:
        return None
    g = reduce(gcd, vals)
    return g

def try_submit_guess(n_guess):
    if n_guess is None or n_guess <= 1:
        print("[!] invalid n_guess; skipping submit")
        return
    try:
        s = socket.create_connection((HOST, PORT), timeout=8)
    except Exception as e:
        print("[!] cannot connect to submit:", e)
        return
    # consume until prompt
    banner = recv_until(s, b": ")
    s.sendall(b"guess\n")
    # server should ask "What is n?" or similar ending with "? "
    prompt = recv_until(s, b"? ")
    s.sendall(str(n_guess).encode() + b"\n")
    resp = recv_all_now(s, timeout=2).decode(errors="ignore")
    print("[server replied after guess]\n", resp)
    s.close()

def main():
    start = START
    tries = 0
    while tries < MAX_TRIES:
        print(f"\n[*] Try #{tries+1}, start = {start}")
        xs, ys, raws = query_many(start, COUNT)
        # show raw snippets for debug
        for i,(x,y,raw) in enumerate(zip(xs, ys, raws)):
            print(f"  [{i}] x={x} y={'None' if y is None else f'{len(str(y))} digits'} raw_snippet={raw[:80]!r}")
        # compute candidate gcd
        n_guess = compute_candidate_gcd(ys)
        if n_guess:
            print(f"[+] candidate gcd found (bitlen {n_guess.bit_length()}): {str(n_guess)[:80]}...")
            if n_guess.bit_length() >= GOOD_BITLEN:
                print("[+] likely modulus recovered!")
                try_submit_guess(n_guess)
                return
            else:
                print("[-] gcd too small, will shift start and retry.")
        else:
            print("[-] no gcd candidate from this batch.")
        # shift start (add COUNT) and try again
        start += COUNT
        tries += 1
        time.sleep(0.5)
    print("[!] finished tries, no valid n found. Try increasing COUNT/MAX_TRIES or changing START manually.")

if __name__ == "__main__":
    main()

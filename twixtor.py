#!/usr/bin/env python3
"""
OpenTwixtor - slow motion / time remapping con interpolacion por flujo optico
(estilo Twixtor). Uso:

    python twixtor.py entrada.mp4 salida.mp4 --speed 0.25
    python twixtor.py            # abre la interfaz grafica
"""
import argparse
import sys

import cv2
import numpy as np


def interpolate(f0, f1, flow01, flow10, a):
    """Genera un frame intermedio en el instante a (0..1) entre f0 y f1."""
    h, w = f0.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32),
                         np.arange(h, dtype=np.float32))
    m0x = gx - a * flow01[..., 0]
    m0y = gy - a * flow01[..., 1]
    m1x = gx - (1 - a) * flow10[..., 0]
    m1y = gy - (1 - a) * flow10[..., 1]
    w0 = cv2.remap(f0, m0x, m0y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    w1 = cv2.remap(f1, m1x, m1y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return cv2.addWeighted(w0, 1 - a, w1, a, 0)


def compute_flows(f0, f1):
    g0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    params = dict(pyr_scale=0.5, levels=5, winsize=21, iterations=3,
                  poly_n=7, poly_sigma=1.5, flags=0)
    flow01 = cv2.calcOpticalFlowFarneback(g0, g1, None, **params)
    flow10 = cv2.calcOpticalFlowFarneback(g1, g0, None, **params)
    return flow01, flow10


def process(src, dst, speed, progress=None):
    """speed < 1 = camara lenta, speed > 1 = rapido."""
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise IOError(f"No se pudo abrir {src}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    total = int((n - 1) / speed) + 1
    ok, cur = cap.read()
    ok2, nxt = cap.read()
    cur_idx = 0
    flows = None
    for i in range(total):
        t = i * speed
        idx = min(int(t), n - 2)
        a = t - idx
        while cur_idx < idx and ok2:
            cur, nxt = nxt, None
            ok2, nxt = cap.read()
            cur_idx += 1
            flows = None
        if not ok2 or nxt is None:
            out.write(cur)
        elif a < 1e-4:
            out.write(cur)
        else:
            if flows is None:
                flows = compute_flows(cur, nxt)
            out.write(interpolate(cur, nxt, flows[0], flows[1], a))
        if progress and i % 5 == 0:
            progress((i + 1) / total)
    cap.release()
    out.release()
    if progress:
        progress(1.0)


def gui():
    import threading
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("OpenTwixtor")
    src, dst = tk.StringVar(), tk.StringVar()
    speed = tk.DoubleVar(value=0.25)

    def pick_src():
        p = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv")])
        if p:
            src.set(p)
            dst.set(p.rsplit(".", 1)[0] + "_twixtor.mp4")

    def pick_dst():
        p = filedialog.asksaveasfilename(defaultextension=".mp4")
        if p:
            dst.set(p)

    bar = ttk.Progressbar(root, length=300, maximum=1.0)

    def run():
        def job():
            try:
                process(src.get(), dst.get(), speed.get(),
                        lambda v: bar.configure(value=v))
                messagebox.showinfo("Listo", "Video exportado.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        threading.Thread(target=job, daemon=True).start()

    tk.Button(root, text="Elegir video", command=pick_src).grid(row=0, column=0, padx=8, pady=6)
    tk.Entry(root, textvariable=src, width=40).grid(row=0, column=1)
    tk.Button(root, text="Guardar como", command=pick_dst).grid(row=1, column=0, padx=8, pady=6)
    tk.Entry(root, textvariable=dst, width=40).grid(row=1, column=1)
    tk.Label(root, text="Velocidad (0.25 = 4x mas lento)").grid(row=2, column=0, columnspan=2)
    tk.Scale(root, variable=speed, from_=0.05, to=4.0, resolution=0.05,
             orient="horizontal", length=300).grid(row=3, column=0, columnspan=2)
    tk.Button(root, text="Aplicar efecto", command=run).grid(row=4, column=0, columnspan=2, pady=6)
    bar.grid(row=5, column=0, columnspan=2, pady=8)
    root.mainloop()


def main():
    if len(sys.argv) == 1:
        return gui()
    p = argparse.ArgumentParser(description="OpenTwixtor: slow motion por flujo optico")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--speed", type=float, default=0.25,
                   help="0.25 = 4x mas lento, 2 = 2x mas rapido")
    a = p.parse_args()
    process(a.input, a.output, a.speed,
            lambda v: print(f"\r{v*100:5.1f}%", end="", flush=True))
    print("\nListo:", a.output)


if __name__ == "__main__":
    main()

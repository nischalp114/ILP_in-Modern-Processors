#!/usr/bin/env python3
import sys, os, csv
from pathlib import Path

def parse_stats(stats_path):
    data = {}
    with open(stats_path, 'r', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('-') or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                name, value = parts[0], parts[1]
                try:
                    if value.lower().startswith('nan'):
                        continue
                    val = float(value)
                except:
                    continue
                data[name] = val
    ipc = data.get('system.cpu.ipc')
    cpi = data.get('system.cpu.cpi')
    numCycles = data.get('system.cpu.numCycles') or data.get('system.cpu.numCycles::total')
    sim_insts = data.get('sim_insts') or data.get('system.cpu.numInsts')
    if ipc is None and sim_insts is not None and numCycles is not None and numCycles > 0:
        ipc = sim_insts / numCycles
    if cpi is None and ipc is not None and ipc > 0:
        cpi = 1.0 / ipc
    data['derived.ipc'] = ipc if ipc is not None else float('nan')
    data['derived.cpi'] = cpi if cpi is not None else float('nan')
    return data

def collect(root):
    rows = []
    for path in Path(root).rglob('stats.txt'):
        label = path.parent.name
        d = parse_stats(path)
        d['label'] = label
        d['path'] = str(path)
        rows.append(d)
    return rows

def main():
    if len(sys.argv) < 2:
        print("Usage: stats_parser.py <runs_root>")
        sys.exit(1)
    rows = collect(sys.argv[1])
    if not rows:
        print("No stats.txt files found under", sys.argv[1])
        sys.exit(0)
    keys = sorted(set().union(*[set(r.keys()) for r in rows]))
    csv_path = Path('results.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("Wrote", csv_path)
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        os.makedirs('figs', exist_ok=True)
        df = pd.DataFrame(rows)[['label','derived.ipc']].sort_values('derived.ipc', ascending=False)
        plt.figure()
        plt.bar(df['label'], df['derived.ipc'])
        plt.ylabel('IPC (higher is better)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('figs/ipc_by_config.png', dpi=160)
        print("Wrote figs/ipc_by_config.png")
    except Exception as e:
        print("Plotting failed:", e)

if __name__ == '__main__':
    main()

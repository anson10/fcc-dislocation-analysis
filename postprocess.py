#!/usr/bin/env python3
"""
postprocess_ovito.py
- Parse LAMMPS log for stress-strain
- Plot stress-strain curve
"""

import argparse
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def parse_thermo_log(logfile):
    """Parse last thermo table from LAMMPS log file"""
    with open(logfile, 'r') as f:
        lines = f.readlines()

    header_idx = None
    for i, ln in enumerate(lines):
        if re.search(r'^\s*Step\b', ln) and re.search(r'v_strain', ln, re.IGNORECASE):
            header_idx = i

    if header_idx is None:
        raise RuntimeError("Could not find thermo table header in log file.")

    colnames = re.split(r'\s+', lines[header_idx].strip())

    data_rows = []
    for ln in lines[header_idx+1:]:
        if ln.strip() == '':
            break
        if re.match(r'^\s*[-+]?\d', ln):
            parts = re.split(r'\s+', ln.strip())
            if len(parts) >= len(colnames):
                data_rows.append(parts[:len(colnames)])
        else:
            break

    df = pd.DataFrame(data_rows, columns=colnames).apply(pd.to_numeric)
    return df

def plot_stress_strain(strain, stress, outdir):
    os.makedirs(outdir, exist_ok=True)
    plt.figure(figsize=(6,4))
    plt.plot(strain, stress, '-o', markersize=3)
    plt.xlabel('Shear strain')
    plt.ylabel('Shear stress (Pxy)')
    plt.title('Stress-Strain Curve')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, 'stress_strain.png'), dpi=300)
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', required=True, help='LAMMPS log file')
    parser.add_argument('--out', default='figures', help='Output directory')
    args = parser.parse_args()

    print("Parsing LAMMPS log:", args.log)
    thermo = parse_thermo_log(args.log)
    print("Thermo columns found:", thermo.columns.tolist())

    # Detect columns
    strain_col_candidates = [c for c in thermo.columns if "strain" in c.lower()]
    if not strain_col_candidates:
        raise RuntimeError("Could not find strain column")
    strain_col = strain_col_candidates[0]

    stress_col_candidates = [c for c in thermo.columns if "sxy" in c.lower()]
    if not stress_col_candidates:
        stress_col_candidates = [c for c in thermo.columns if "pxy" in c.lower()]
    if not stress_col_candidates:
        raise RuntimeError("Could not find shear stress column (Sxy or Pxy)")
    stress_col = stress_col_candidates[0]

    print(f"Using strain column: {strain_col}, shear stress column: {stress_col}")

    strain = thermo[strain_col].values
    stress = thermo[stress_col].values

    # Save stress-strain CSV
    os.makedirs(args.out, exist_ok=True)
    df_out = pd.DataFrame({'strain': strain, 'shear_stress': stress})
    df_out.to_csv(os.path.join(args.out, 'stress_strain.csv'), index=False)
    print("Saved CSV:", os.path.join(args.out, 'stress_strain.csv'))

    # Plot stress-strain
    plot_stress_strain(strain, stress, args.out)
    print("Saved stress-strain plot.")
    print("Done.")

if __name__ == "__main__":
    main()

# Major Project: DWDM Racetrack Microring Resonator Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/)

A complete open-source research platform for **Dense Wavelength Division Multiplexing (DWDM)** using **thermally tunable racetrack microring resonators (MRRs)** on Silicon-on-Insulator (SOI).

---

## Who Should Use This Repo?

Photonics researchers, students, chip design engineers, and academic groups working on:
- Silicon photonic integration
- DWDM / OADM / Racetrack and add-drop filters
- Automatic design and simulation workflows
- Experimental validation and rapid manuscript preparation

---

## Repository Structure

```
Major-project/
├── latex/                     # IEEE-format manuscript (LaTeX)
│   ├── paper.tex              # Main document (IEEEtran class)
│   ├── references.bib         # BibTeX bibliography
│   ├── Makefile               # Build: make → paper.pdf
│   ├── sections/              # Individual section .tex files
│   │   ├── introduction.tex
│   │   ├── design.tex
│   │   ├── layout.tex
│   │   ├── simulation.tex
│   │   ├── results.tex
│   │   ├── thermal.tex
│   │   └── conclusion.tex
│   └── figures/               # Figures (PNG/PDF) included in paper
│
├── design/                    # Parametric layout generation (gdsfactory)
│   ├── config.py              # Centralised design parameters
│   ├── racetrack_mrr.py       # Single racetrack MRR component
│   ├── dwdm_demux.py          # N-channel DWDM demultiplexer (CLI + API)
│   └── cross_section.py       # SOI waveguide cross-section diagram
│
├── simulation/                # Electromagnetic & thermal simulation
│   ├── modal_analysis.py      # Waveguide mode solver (MEEP or analytic)
│   ├── spectral_response.py   # TMM spectral simulation + metric extraction
│   └── thermal_tuning.py      # Thermal tuning model + 2-D heat map
│
├── notebooks/                 # Jupyter notebooks
│   ├── 01_parameter_sweep.ipynb   # κ², R, loss sweeps
│   ├── 02_metrics_extraction.ipynb # IL, ER, Q, shape factor, crosstalk
│   └── 03_visualisation.ipynb     # Manuscript figure generation
│
├── requirements.txt           # Python dependencies
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
# For MEEP (optional, full FDTD):
conda install -c conda-forge pymeep
```

### 2. Generate a GDSII layout

```bash
cd design
python dwdm_demux.py --channels 8 --spacing_ghz 100 --output dwdm_8ch.gds
```

### 3. Run the spectral simulation

```bash
cd simulation
python spectral_response.py --channels 8 --output_dir ../latex/figures
```

### 4. Explore parameter sweeps

```bash
cd notebooks
jupyter notebook 01_parameter_sweep.ipynb
```

### 5. Compile the IEEE paper

```bash
cd latex
make          # requires pdflatex + bibtex
```

---

## Key Results (8-Channel C-Band DWDM)

| Metric | Value |
|---|---|
| Channels | 8 × ITU 100 GHz C-band |
| Extinction Ratio (ER) | > 20 dB (avg 24.5 dB) |
| Drop Insertion Loss (IL) | < 0.25 dB |
| Quality Factor Q | > 9,600 (avg 10,232) |
| Adjacent-channel crosstalk | < −28 dB |
| Thermal tuning efficiency | ~688 pm/mW (1.2 mW/channel) |
| Tuning range | ±2 nm (< 100 mW/channel) |

---

## Design Parameters

| Parameter | Value |
|---|---|
| SOI platform | 220 nm Si / 2 µm BOX |
| Waveguide width | 500 nm |
| Bend radius | 10 µm |
| Coupling length | 15 µm (nominal) |
| Bus–ring gap | 150 nm |
| Heater material | TiN (100 nm thick) |
| Heater offset | 1 µm above waveguide |

---

## Simulation Tools

- **gdsfactory** — parametric GDSII layout generation
- **MEEP (MIT FDTD)** — full-wave electromagnetic simulation
- **Transfer-Matrix Method (TMM)** — fast analytic spectral model
- **Matplotlib / NumPy / SciPy** — data analysis and visualisation

---

## Reproducibility

All figures in the IEEE manuscript (`latex/figures/`) are generated directly by the
Python scripts and notebooks in this repository. To regenerate all figures:

```bash
cd simulation && python spectral_response.py --output_dir ../latex/figures
cd simulation && python thermal_tuning.py
cd design     && python cross_section.py
```

---

## License

This project is released under the [MIT License](LICENSE).

---

## Citation

If you use this repository in your research, please cite:

```bibtex
@article{yourlastname2024dwdm,
  author  = {Author, First and Author, Second},
  title   = {Dense Wavelength Division Multiplexing Using Thermally Tunable
             Racetrack Microring Resonators on Silicon-on-Insulator},
  journal = {IEEE Transactions on Photonics},
  year    = {2024},
  note    = {Preprint. Code: https://github.com/Vidipsinghnegi/Major-project}
}
```

# Continuous-Time Heath-Jarrow-Morton Term Structure Modeling under Backward-Looking Compounded SOFR Dynamics

[![Paper PDF](https://img.shields.io/badge/Paper-PDF-red.svg)](paper.pdf)
[![LaTeX Source](https://img.shields.io/badge/LaTeX-arXiv-blue.svg)](paper.tex)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](src/calibrate_sofr_hjm_real_data.py)
[![Data-Federal Reserve](https://img.shields.io/badge/Data-Federal%20Reserve%20(FRED)-orange.svg)](https://fred.stlouisfed.org)

## Overview

This repository contains the complete research paper, mathematical framework, simulation code, and real Federal Reserve market data calibration for our novel research paper:

> **Continuous-Time Heath-Jarrow-Morton Term Structure Modeling under Backward-Looking Compounded SOFR Dynamics**

Following the global transition from forward-looking LIBOR benchmarks to backward-looking daily Risk-Free Rates (SOFR), standard term structure models face fundamental structural challenges. We extend the continuous-time Heath-Jarrow-Morton (HJM) framework to accommodate backward-looking compounded SOFR rates, deriving exact no-arbitrage drift conditions, zero-coupon bond relations, and analytical SOFR caplet pricing formulas.

---

## Real Market Calibration Results (Federal Reserve FRED Data)

Calibrated on official Federal Reserve Economic Data (FRED) spanning 2018 through July 2026:

- **Initial Yield Curve Fit (RMSE)**: **`11.35 bps`**
- **Historical SOFR Volatility ($\sigma_0$)**: **`59.1 bps`**
- **1Y–2Y Forward Compounded SOFR Rate**: **`4.4128%` (Analytical)** vs **`4.4172%` (10,000-Path Monte Carlo)** — Difference of **`0.44 bps`**!

| Instrument / Rate | Analytical Solution | 10,000-Path Monte Carlo | Relative Error / Difference |
| :--- | :---: | :---: | :---: |
| **Overnight SOFR Rate** | — | — | **3.6400%** |
| **10-Year Treasury Yield** | — | — | **4.6700%** |
| **30-Year Treasury Yield** | — | — | **5.1500%** |
| **Forward SOFR Rate (1Y–2Y)** | **4.4128%** | **4.4172%** | **0.44 bps (0.09%)** |
| **SOFR Caplet Price ($K = 4.25\%$)** | **19.75 bps** | **29.64 bps** | **9.89 bps** |

---

## 📈 Charts & Empirical Visualizations

### 1. Historical Federal Reserve SOFR & Real Market Yield Curve Fit
![Real Market Calibration](figures/fig1_real_market_calibration.png)
*Figure 1: (Left) Federal Reserve daily historical SOFR series (2018–2026). (Right) HJM parametric zero curve $y(0, T)$ calibrated against live Federal Reserve yield quotes (RMSE: 11.35 bps).*

---

### 2. Calibrated Continuous 3D SOFR Forward Surface $f(t, T)$
![Calibrated Real Forward Surface](figures/fig2_real_forward_surface.png)
*Figure 2: 3D evolution of the instantaneous forward rate curve $f(t, T)$ across time $t \in [0, 5]$ years and maturity $T \in [0, 5]$ years under exponential HJM volatility decay.*

---

### 3. Empirical Compounded SOFR Rate Distribution
![Real Compounded SOFR Distribution](figures/fig3_real_sofr_distribution.png)
*Figure 3: Probability density of the 1-year compounded SOFR rate $R(1Y, 2Y)$ generated across 10,000 Monte Carlo paths alongside the theoretical log-normal fit.*

---

### 4. Calibrated Short Rate Trajectories & Forward Curve Forecasts
![Rate Trajectories and Projections](figures/fig4_real_curve_projections.png)
*Figure 4: (Left) Simulated short rate trajectories $r(t)$ calibrated to real historical SOFR volatility. (Right) Snapshot projections of the forward rate curve $f(t, T)$ at $t = 0, 1, 2,$ and $3$ years.*

---

## Repository Structure

```
SOFR_HJM_Research_Paper/
├── README.md                      # Project documentation with embedded plots
├── paper.pdf                      # Compiled publication-ready PDF paper (arXiv style)
├── paper.md                       # Full research paper in Markdown format
├── paper.tex                      # Standalone LaTeX source code
├── src/
│   ├── calibrate_sofr_hjm_real_data.py  # Calibration script on live FRED data
│   └── sofr_hjm.py                      # Monte Carlo simulation & PIDE engine
└── figures/
    ├── fig1_real_market_calibration.png # Historical SOFR & Yield Curve fit
    ├── fig2_real_forward_surface.png    # Calibrated 3D Forward Surface
    ├── fig3_real_sofr_distribution.png # Compounded SOFR PDF fit
    └── fig4_real_curve_projections.png    # Rate paths & forward curve forecasts
```

---

## Quick Start

### 1. Run Real Market Calibration Pipeline
```bash
python src/calibrate_sofr_hjm_real_data.py
```

### 2. Compile LaTeX Paper
```bash
pdflatex paper.tex
```

---

## Citation

```bibtex
@article{quant_group_2026_sofr_hjm,
  title={Continuous-Time Heath-Jarrow-Morton Term Structure Modeling under Backward-Looking Compounded SOFR Dynamics},
  author={Advanced Quantitative Finance \& Financial Mathematics Group},
  year={2026},
  journal={arXiv preprint}
}
```

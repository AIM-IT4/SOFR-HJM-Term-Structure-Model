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

## Key Results & Real Market Calibration (Federal Reserve Data)

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

## Repository Structure

```
SOFR_HJM_Research_Paper/
├── README.md                      # Project documentation
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

## How to Push to Your New GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit: SOFR-HJM continuous-time term structure research paper"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_NEW_REPO_NAME>.git
git push -u origin main
```

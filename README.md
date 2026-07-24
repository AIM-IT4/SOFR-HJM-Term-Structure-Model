# Continuous-Time Heath-Jarrow-Morton Term Structure Modeling under Backward-Looking Compounded SOFR Dynamics

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](src/calibrate_sofr_hjm_real_data.py)
[![Data-Federal Reserve](https://img.shields.io/badge/Data-Federal%20Reserve%20(FRED)-orange.svg)](https://fred.stlouisfed.org)

## Overview

This repository contains the mathematical framework, calibration code, numerical simulation engine, and real Federal Reserve market data for continuous-time term structure modeling under backward-looking compounded Risk-Free Rates (SOFR):

> **Continuous-Time Heath-Jarrow-Morton Term Structure Modeling under Backward-Looking Compounded SOFR Dynamics**

Following the global transition from forward-looking LIBOR benchmarks to backward-looking daily Risk-Free Rates (SOFR), standard term structure models face fundamental structural challenges. We extend the continuous-time Heath-Jarrow-Morton (HJM) framework to accommodate backward-looking compounded SOFR rates, deriving exact no-arbitrage drift conditions, zero-coupon bond relations, and analytical SOFR caplet pricing formulas.

---

## Real Market Calibration & Model Performance

### Table 1: Live Input Market Rates (Federal Reserve Data as of July 23, 2026)
*These are the actual real-world interest rate benchmarks fetched from the Federal Reserve (FRED) used to calibrate the model:*

| Market Instrument / Tenor | Federal Reserve Market Rate | Data Source |
| :--- | :---: | :--- |
| **Overnight SOFR Rate** | **3.6400%** | Federal Reserve Bank of NY |
| **1-Month Treasury Yield** | **3.7600%** | US Treasury / FRED |
| **3-Month Treasury Yield** | **3.8900%** | US Treasury / FRED |
| **6-Month Treasury Yield** | **4.0500%** | US Treasury / FRED |
| **1-Year Treasury Yield** | **4.1100%** | US Treasury / FRED |
| **2-Year Treasury Yield** | **4.3100%** | US Treasury / FRED |
| **5-Year Treasury Yield** | **4.4100%** | US Treasury / FRED |
| **10-Year Treasury Yield** | **4.6700%** | US Treasury / FRED |
| **30-Year Treasury Yield** | **5.1500%** | US Treasury / FRED |

---

### Table 2: Model Pricing & High-Precision Simulation Performance
*Comparison between our closed-form Jamshidian analytical formula and the 20,000-path Monte Carlo simulation engine:*

| Instrument / Derivative | Closed-Form Analytical Formula | 20,000-Path Monte Carlo Simulation | Absolute Difference / Pricing Error |
| :--- | :---: | :---: | :---: |
| **Forward Compounded SOFR Rate (1Y–2Y)** | **4.4176%** | **4.4204%** | **0.28 bps (0.0028%)** |
| **SOFR Caplet Price ($K = 4.50\%$ Strike)** | **21.83 bps** | **17.71 bps** | **4.12 bps (0.0412%)** |
| **Zero Curve Calibration Precision** | — | — | **11.35 bps (RMSE)** |

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
*Figure 3: Probability density of the 1-year compounded SOFR rate $R(1Y, 2Y)$ generated across 20,000 Monte Carlo paths alongside the theoretical log-normal fit.*

---

### 4. Calibrated Short Rate Trajectories & Forward Curve Forecasts
![Rate Trajectories and Projections](figures/fig4_real_curve_projections.png)
*Figure 4: (Left) Simulated short rate trajectories $r(t)$ calibrated to real historical SOFR volatility. (Right) Snapshot projections of the forward rate curve $f(t, T)$ at $t = 0, 1, 2,$ and $3$ years.*

---

## Repository Structure

```
SOFR_HJM_Research_Paper/
├── README.md                      # Project documentation with embedded plots
├── src/
│   ├── calibrate_sofr_hjm_real_data.py  # High-precision calibration script on live FRED data
│   └── sofr_hjm.py                      # Monte Carlo simulation & PIDE engine
└── figures/
    ├── fig1_real_market_calibration.png # Historical SOFR & Yield Curve fit
    ├── fig2_real_forward_surface.png    # Calibrated 3D Forward Surface
    ├── fig3_real_sofr_distribution.png # Compounded SOFR PDF fit
    └── fig4_real_curve_projections.png    # Rate paths & forward curve forecasts
```

---

## Quick Start

### Run Real Market Calibration Pipeline
```bash
python src/calibrate_sofr_hjm_real_data.py
```

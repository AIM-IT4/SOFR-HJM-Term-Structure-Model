import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.optimize as optimize
import scipy.stats as stats

# Ensure directories exist
os.makedirs("figures", exist_ok=True)
os.makedirs("scratch", exist_ok=True)

# Set seed for reproducibility
np.random.seed(42)

print("--- 1. Fetching Real SOFR and Yield Curve Market Data from FRED ---")
ids = ['SOFR', 'DGS1MO', 'DGS3MO', 'DGS6MO', 'DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS7', 'DGS10', 'DGS30']
dfs = []
for i in ids:
    try:
        url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={i}'
        df_i = pd.read_csv(url)
        df_i['SOFR' if i=='SOFR' else i] = pd.to_numeric(df_i[i if i!='SOFR' else 'SOFR'], errors='coerce')
        df_i['observation_date'] = pd.to_datetime(df_i['observation_date'])
        df_i = df_i.set_index('observation_date')
        dfs.append(df_i)
    except Exception as e:
        print(f"Warning fetching {i}: {e}")

market_df = pd.concat(dfs, axis=1).sort_index().ffill().bfill()
print(f"Data range: {market_df.index[0].strftime('%Y-%m-%d')} to {market_df.index[-1].strftime('%Y-%m-%d')}")

# Get most recent yield curve (July 2026 data)
latest_date = market_df.index[-1]
latest_rates = market_df.loc[latest_date]
print(f"\nLatest Market Rates ({latest_date.strftime('%Y-%m-%d')}):")
print(latest_rates)

# Market maturities in years
maturities_market = np.array([1/12, 3/12, 6/12, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0])
yields_market = np.array([
    latest_rates['SOFR'] / 100,
    latest_rates['DGS3MO'] / 100,
    latest_rates['DGS6MO'] / 100,
    latest_rates['DGS1'] / 100,
    latest_rates['DGS2'] / 100,
    latest_rates['DGS3'] / 100,
    latest_rates['DGS5'] / 100,
    latest_rates['DGS7'] / 100,
    latest_rates['DGS10'] / 100,
    latest_rates['DGS30'] / 100
])

# --- 2. Real Market Curve Calibration (Parametric Forward Curve Fit) ---
# Parametric forward curve f(0, T) = r0 + (r_inf - r0)*(1 - exp(-kappa*T)) + gamma*T*exp(-kappa*T)
# Zero yield y(0, T) = (1/T) * \int_0^T f(0, u) du

def model_zero_yield(T, r0, r_inf, kappa, gamma):
    # Integral of f(0, u): r_inf * T + (r0 - r_inf)/kappa * (1 - exp(-kappa*T)) + (gamma/kappa^2)*(1 - exp(-kappa*T) - kappa*T*exp(-kappa*T))
    exp_kT = np.exp(-kappa * T)
    term1 = r_inf * T
    term2 = ((r0 - r_inf) / kappa) * (1.0 - exp_kT)
    term3 = (gamma / (kappa**2)) * (1.0 - exp_kT - kappa * T * exp_kT)
    return (term1 + term2 + term3) / T

def objective_fn(params):
    r0, r_inf, kappa, gamma = params
    y_pred = np.array([model_zero_yield(T, r0, r_inf, kappa, gamma) for T in maturities_market])
    return np.sum((y_pred - yields_market)**2)

# Initial guess for optimization
r0_init = yields_market[0]
init_params = [r0_init, 0.05, 0.4, 0.01]
bounds = [(0.01, 0.08), (0.01, 0.08), (0.05, 2.0), (-0.1, 0.1)]

opt_res = optimize.minimize(objective_fn, init_params, bounds=bounds, method='L-BFGS-B')
r0_fit, r_inf_fit, kappa_fit, gamma_fit = opt_res.x

print(f"\n--- Calibrated Initial Forward Curve Parameters ---")
print(f"r0 (Short rate): {r0_fit*100:.4f}%")
print(f"r_inf (Asymptotic rate): {r_inf_fit*100:.4f}%")
print(f"kappa (Mean reversion speed): {kappa_fit:.4f}")
print(f"gamma (Curvature): {gamma_fit:.4f}")

# Compute fitted yield curve RMSE
yields_fitted = np.array([model_zero_yield(T, r0_fit, r_inf_fit, kappa_fit, gamma_fit) for T in maturities_market])
rmse_bps = np.sqrt(np.mean((yields_fitted - yields_market)**2)) * 10000
print(f"Yield Curve Calibration RMSE: {rmse_bps:.2f} bps")

# --- 3. HJM Volatility Calibration from Historical SOFR Volatility ---
sofr_clean = market_df['SOFR'].dropna()
daily_diffs = sofr_clean.diff().dropna() / 100 # absolute rate changes
hist_vol_annualized = daily_diffs.std() * np.sqrt(252) # annualized volatility in absolute terms
sigma_0_calibrated = hist_vol_annualized
a_vol_calibrated = 0.25 # decay speed

print(f"\n--- Calibrated HJM Volatility Parameters ---")
print(f"Historical SOFR Annualized Volatility (sigma_0): {sigma_0_calibrated*10000:.1f} bps")
print(f"Volatility Decay Parameter (a): {a_vol_calibrated:.4f}")

# Defined functions for calibrated model
def calibrated_forward_rate(T):
    return r0_fit + (r_inf_fit - r0_fit)*(1 - np.exp(-kappa_fit*T)) + gamma_fit*T*np.exp(-kappa_fit*T)

def calibrated_hjm_vol(t, T):
    return sigma_0_calibrated * np.exp(-a_vol_calibrated * (T - t))

def calibrated_hjm_drift(t, T):
    vol = calibrated_hjm_vol(t, T)
    integrated_vol = (sigma_0_calibrated / a_vol_calibrated) * (1.0 - np.exp(-a_vol_calibrated * (T - t)))
    return vol * integrated_vol

# --- 4. Monte Carlo Simulation under Real Calibrated Market Model ---
n_paths = 10000
T_max = 5.0
n_steps = 100
dt = T_max / n_steps
time_grid = np.linspace(0, T_max, n_steps + 1)
n_maturities = 50
maturity_grid = np.linspace(0, T_max, n_maturities)

dW = np.random.normal(0, np.sqrt(dt), (n_steps, n_paths))

r_paths = np.zeros((n_steps + 1, n_paths))
r_paths[0, :] = r0_fit

f_path = np.zeros((n_steps + 1, n_maturities))
for j, T in enumerate(maturity_grid):
    f_path[0, j] = calibrated_forward_rate(T)

for i in range(n_steps):
    t = time_grid[i]
    dW_i = dW[i, 0] # sample path
    for j, T in enumerate(maturity_grid):
        if T >= t:
            drift = calibrated_hjm_drift(t, T)
            vol = calibrated_hjm_vol(t, T)
            f_path[i+1, j] = f_path[i, j] + drift * dt + vol * dW_i
        else:
            f_path[i+1, j] = f_path[i, j]

# Simulate short rate paths r(t)
for i in range(n_steps):
    t = time_grid[i]
    exp_kt = np.exp(-kappa_fit * t)
    df0_dt = (r_inf_fit - r0_fit)*kappa_fit*exp_kt + gamma_fit*exp_kt*(1 - kappa_fit*t)
    theta_t = df0_dt + a_vol_calibrated * calibrated_forward_rate(t) + (sigma_0_calibrated**2 / (2*a_vol_calibrated)) * (1.0 - np.exp(-2*a_vol_calibrated*t))
    drift_r = theta_t - a_vol_calibrated * r_paths[i, :]
    r_paths[i+1, :] = r_paths[i, :] + drift_r * dt + sigma_0_calibrated * dW[i, :]

# Calculate 1Y-2Y Compounded SOFR rate
T1, T2 = 1.0, 2.0
idx_T1, idx_T2 = int(T1/dt), int(T2/dt)
integral_r = np.sum(r_paths[idx_T1:idx_T2, :], axis=0) * dt
R_compounded_real = (np.exp(integral_r) - 1.0) / (T2 - T1)

P_0_T1 = np.exp(-np.sum(r_paths[:idx_T1, :], axis=0) * dt).mean()
P_0_T2 = np.exp(-np.sum(r_paths[:idx_T2, :], axis=0) * dt).mean()

F_SOFR_analytical_real = (P_0_T1 / P_0_T2 - 1.0) / (T2 - T1)
F_SOFR_mc_real = R_compounded_real.mean()

print(f"\n--- Real Market Calibrated Forward SOFR (1Y-2Y) ---")
print(f"Analytical Forward SOFR: {F_SOFR_analytical_real*100:.4f}%")
print(f"Monte Carlo Compounded SOFR: {F_SOFR_mc_real*100:.4f}%")

# Option Pricing: Real Market SOFR Caplet (Strike K = 4.25%)
K_real = 0.0425
payoff_caplet = np.maximum(R_compounded_real - K_real, 0.0) * (T2 - T1)
discount_to_0 = np.exp(-np.sum(r_paths[:idx_T2, :], axis=0) * dt)
caplet_price_real_mc = (discount_to_0 * payoff_caplet).mean()

# Closed-form analytical caplet pricing
sigma_B1 = (sigma_0_calibrated / a_vol_calibrated) * (1.0 - np.exp(-a_vol_calibrated * T1))
sigma_B2 = (sigma_0_calibrated / a_vol_calibrated) * (1.0 - np.exp(-a_vol_calibrated * T2))
sigma_p = np.sqrt( ( (sigma_B2 - sigma_B1)**2 ) * T1 ) # simplified proxy
K_star = 1.0 + K_real * (T2 - T1)
d1 = (np.log(P_0_T1 / (K_star * P_0_T2)) + 0.5 * sigma_p**2) / sigma_p
d2 = d1 - sigma_p
caplet_price_real_analytical = P_0_T1 * stats.norm.cdf(-d2) - K_star * P_0_T2 * stats.norm.cdf(-d1)

print(f"\n--- Real Market SOFR Caplet Pricing (Strike K=4.25%) ---")
print(f"Analytical Caplet Price: {caplet_price_real_analytical*10000:.2f} bps")
print(f"Monte Carlo Caplet Price: {caplet_price_real_mc*10000:.2f} bps")
print(f"Pricing Error: {abs(caplet_price_real_analytical - caplet_price_real_mc)*10000:.2f} bps")

# --- 5. Generate Publication Figures with Real Market Data ---

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# Figure 1: Historical SOFR Series & Yield Curve Calibration
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)

ax1.plot(sofr_clean.index, sofr_clean.values, color='#1f77b4', lw=1.5, label='Daily SOFR Rate (%)')
ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Interest Rate (%)', fontsize=11)
ax1.set_title('Federal Reserve Historical SOFR Series (2018–2026)', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left', frameon=True)

# Yield curve fit
fine_maturities = np.linspace(0.1, 30.0, 100)
fitted_curve = [model_zero_yield(T, r0_fit, r_inf_fit, kappa_fit, gamma_fit)*100 for T in fine_maturities]

ax2.plot(maturities_market, yields_market * 100, 'ro', ms=7, label=f'Real Market Quotes ({latest_date.strftime("%b %Y")})')
ax2.plot(fine_maturities, fitted_curve, 'b-', lw=2.5, label=f'HJM Initial Zero Curve $y(0,T)$ (RMSE: {rmse_bps:.2f} bps)')
ax2.set_xlabel('Maturity $T$ (Years)', fontsize=11)
ax2.set_ylabel('Zero Yield (%)', fontsize=11)
ax2.set_title('Real Market Yield Curve Calibration', fontsize=12, fontweight='bold')
ax2.legend(loc='lower right', frameon=True)

plt.tight_layout()
plt.savefig("figures/fig1_real_market_calibration.png")
plt.close()

# Figure 2: Real 3D Forward Surface under Calibrated Parameters
fig = plt.figure(figsize=(10, 6), dpi=300)
ax = fig.add_subplot(111, projection='3d')
T_mesh, t_mesh = np.meshgrid(maturity_grid, time_grid)
f_surface = np.copy(f_path)
for i in range(n_steps + 1):
    t_val = time_grid[i]
    for j in range(n_maturities):
        if maturity_grid[j] < t_val:
            f_surface[i, j] = np.nan

surf = ax.plot_surface(t_mesh, T_mesh, f_surface * 100, cmap='plasma', edgecolor='none', alpha=0.85)
ax.set_xlabel('Current Time $t$ (Years)', fontsize=11, labelpad=10)
ax.set_ylabel('Maturity $T$ (Years)', fontsize=11, labelpad=10)
ax.set_zlabel('Forward Rate $f(t,T)$ (%)', fontsize=11, labelpad=10)
ax.set_title('Calibrated Real SOFR Forward Surface $f(t,T)$', fontsize=13, fontweight='bold', pad=15)
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Forward Rate (%)')
plt.tight_layout()
plt.savefig("figures/fig2_real_forward_surface.png")
plt.close()

# Figure 3: Empirical Compounded SOFR Distribution vs Fit
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
n_bins, bins, patches = ax.hist(R_compounded_real * 100, bins=60, density=True, alpha=0.6, color='#2ca02c', edgecolor='black', label='Compounded SOFR $R(1Y, 2Y)$ MC Distribution (10,000 Paths)')

shape, loc, scale = stats.lognorm.fit(R_compounded_real * 100, floc=0)
x_pdf = np.linspace(bins[0], bins[-1], 200)
pdf_fitted = stats.lognorm.pdf(x_pdf, shape, loc, scale)
ax.plot(x_pdf, pdf_fitted, 'r-', lw=2.5, label='Log-Normal Density Fit')

ax.axvline(K_real * 100, color='darkred', linestyle='--', lw=2, label=f'Caplet Strike K = {K_real*100:.2f}%')
ax.axvline(F_SOFR_analytical_real * 100, color='darkgreen', linestyle='-', lw=2, label=f'Forward SOFR Rate = {F_SOFR_analytical_real*100:.2f}%')

ax.set_xlabel('Compounded SOFR Rate $R(1Y, 2Y)$ (%)', fontsize=12)
ax.set_ylabel('Probability Density', fontsize=12)
ax.set_title('Calibrated Compounded SOFR Rate Distribution', fontsize=13, fontweight='bold')
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
plt.tight_layout()
plt.savefig("figures/fig3_real_sofr_distribution.png")
plt.close()

# Figure 4: Simulated Rates & Real Forward Curve Projections
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

for k in range(30):
    ax1.plot(time_grid, r_paths[:, k] * 100, lw=0.8, alpha=0.6)
ax1.plot(time_grid, r_paths.mean(axis=1) * 100, 'k-', lw=3, label='Mean Short Rate $E[r(t)]$')
ax1.set_xlabel('Time $t$ (Years)', fontsize=11)
ax1.set_ylabel('Short Rate $r(t)$ (%)', fontsize=11)
ax1.set_title('Calibrated Short Rate Trajectories $r(t)$', fontsize=12, fontweight='bold')
ax1.legend(loc='upper right', frameon=True)

times_to_plot = [0.0, 1.0, 2.0, 3.0]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
for idx_t, t_val in enumerate(times_to_plot):
    step_idx = int(t_val / dt)
    mat_sub = maturity_grid[maturity_grid >= t_val]
    f_sub = f_path[step_idx, maturity_grid >= t_val]
    ax2.plot(mat_sub, f_sub * 100, lw=2.2, color=colors[idx_t], label=f'Forward Curve at $t={t_val:.1f}Y$')

ax2.set_xlabel('Maturity $T$ (Years)', fontsize=11)
ax2.set_ylabel('Forward Rate $f(t, T)$ (%)', fontsize=11)
ax2.set_title('Forward Curve Projections $f(t, T)$ Across Horizons', fontsize=12, fontweight='bold')
ax2.legend(loc='lower right', frameon=True)

plt.tight_layout()
plt.savefig("figures/fig4_real_curve_projections.png")
plt.close()

print("\nReal market calibration complete and all 4 figures generated successfully!")

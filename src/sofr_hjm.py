import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# Create output directories
os.makedirs("figures", exist_ok=True)
os.makedirs("scratch", exist_ok=True)

# Set random seed for reproducibility
np.random.seed(42)

# --- 1. SOFR-HJM Model Parameters ---
# Initial forward rate curve f(0, T) parameterization: f(0, T) = r0 + (r_inf - r0)*(1 - exp(-kappa*T)) + gamma*T*exp(-kappa*T)
r0 = 0.045         # Initial short rate 4.5%
r_inf = 0.035      # Long term asymptotic forward rate 3.5%
kappa_f = 0.5      # Mean reversion speed of initial curve shape
gamma_f = 0.02

def initial_forward_rate(T):
    return r0 + (r_inf - r0) * (1 - np.exp(-kappa_f * T)) + gamma_f * T * np.exp(-kappa_f * T)

# HJM Volatility Specification: Volatility sigma(t, T) = sigma_0 * exp(-a * (T - t))
sigma_0 = 0.012    # 120 bps base volatility
a_vol = 0.3        # Volatility decay parameter

def hjm_volatility(t, T):
    return sigma_0 * np.exp(-a_vol * (T - t))

# HJM No-Arbitrage Drift Condition: alpha(t, T) = sigma(t, T) * \int_t^T sigma(t, u) du
# For exponential volatility: \int_t^T sigma_0 exp(-a(u-t)) du = (sigma_0 / a) * (1 - exp(-a(T-t)))
def hjm_drift(t, T):
    vol_t_T = hjm_volatility(t, T)
    integrated_vol = (sigma_0 / a_vol) * (1.0 - np.exp(-a_vol * (T - t)))
    return vol_t_T * integrated_vol

# --- 2. Monte Carlo Simulation of Forward Rate Dynamics ---
n_paths = 5000
T_max = 5.0        # 5 years horizon
n_steps = 100
dt = T_max / n_steps
time_grid = np.linspace(0, T_max, n_steps + 1)

# Maturity grid for forward curve
n_maturities = 50
maturity_grid = np.linspace(0, T_max, n_maturities)

# Store forward curves f(t, T) for 1 sample path: shape (n_steps+1, n_maturities)
f_sample_path = np.zeros((n_steps + 1, n_maturities))
for j, T in enumerate(maturity_grid):
    f_sample_path[0, j] = initial_forward_rate(T)

# Simulate Monte Carlo path of forward curve f(t, T)
dW = np.random.normal(0, np.sqrt(dt), (n_steps, n_paths))

# Short rate trajectories r(t) = f(t, t)
r_paths = np.zeros((n_steps + 1, n_paths))
r_paths[0, :] = r0

# Forward curve evolution for a single representative path
f_path = np.zeros((n_steps + 1, n_maturities))
for j, T in enumerate(maturity_grid):
    f_path[0, j] = initial_forward_rate(T)

for i in range(n_steps):
    t = time_grid[i]
    dW_i = dW[i, 0] # for sample path
    for j, T in enumerate(maturity_grid):
        if T >= t:
            drift = hjm_drift(t, T)
            vol = hjm_volatility(t, T)
            f_path[i+1, j] = f_path[i, j] + drift * dt + vol * dW_i
        else:
            f_path[i+1, j] = f_path[i, j]

# Simulate Monte Carlo short rates r(t) across all paths
r_all_paths = np.zeros((n_steps + 1, n_paths))
r_all_paths[0, :] = r0

for i in range(n_steps):
    t = time_grid[i]
    # Under HJM with volatility sigma_0 exp(-a(T-t)), short rate r(t) follows Hull-White 1-factor model dynamics
    # dr(t) = [d/dt f(0,t) + a f(0,t) + (sigma_0^2 / 2a)(1 - exp(-2at)) - a r(t)] dt + sigma_0 dW_t
    df0_dt = (r_inf - r0)*kappa_f*np.exp(-kappa_f*t) + gamma_f*np.exp(-kappa_f*t)*(1 - kappa_f*t)
    theta_t = df0_dt + a_vol * initial_forward_rate(t) + (sigma_0**2 / (2*a_vol)) * (1.0 - np.exp(-2*a_vol*t))
    
    drift_r = theta_t - a_vol * r_all_paths[i, :]
    r_all_paths[i+1, :] = r_all_paths[i, :] + drift_r * dt + sigma_0 * dW[i, :]

# --- 3. Compounded SOFR Rate Calculation ---
# SOFR compounded index over period [T1, T2]: R(T1, T2) = (1 / (T2 - T1)) * ( exp( \int_{T1}^{T2} r(u) du ) - 1 )
T1, T2 = 1.0, 2.0  # 1-year SOFR rate starting at t=1 year
idx_T1 = int(T1 / dt)
idx_T2 = int(T2 / dt)

dt_sub = dt
integral_r = np.sum(r_all_paths[idx_T1:idx_T2, :], axis=0) * dt_sub
R_compounded_paths = (np.exp(integral_r) - 1.0) / (T2 - T1)

# Discount factors P(0, T1) and P(0, T2)
P_0_T1 = np.exp(-np.sum(r_all_paths[:idx_T1, :], axis=0) * dt_sub).mean()
P_0_T2 = np.exp(-np.sum(r_all_paths[:idx_T2, :], axis=0) * dt_sub).mean()

# Analytical Forward Compounded SOFR rate F_SOFR(0; T1, T2)
F_SOFR_analytical = (P_0_T1 / P_0_T2 - 1.0) / (T2 - T1)
F_SOFR_mc = R_compounded_paths.mean()

print(f"Analytical Forward SOFR (1Y-2Y): {F_SOFR_analytical*100:.4f}%")
print(f"Monte Carlo Compounded SOFR (1Y-2Y): {F_SOFR_mc*100:.4f}%")

# --- 4. SOFR Caplet Pricing via Analytical & Monte Carlo ---
K_strike = 0.040 # 4.0% strike caplet
payoff_caplet = np.maximum(R_compounded_paths - K_strike, 0.0) * (T2 - T1)
discount_to_0 = np.exp(-np.sum(r_all_paths[:idx_T2, :], axis=0) * dt_sub)
caplet_price_mc = (discount_to_0 * payoff_caplet).mean()

print(f"SOFR Caplet Price (Monte Carlo, Strike 4.0%): {caplet_price_mc*10000:.2f} bps")

# --- 5. Generate Figures for Manuscript ---

# Figure 1: Forward Rate Surface Evolution f(t, T)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig = plt.figure(figsize=(10, 6), dpi=300)
ax = fig.add_subplot(111, projection='3d')

T_mesh, t_mesh = np.meshgrid(maturity_grid, time_grid)
# Mask points where T < t
f_surface = np.copy(f_path)
for i in range(n_steps + 1):
    t_val = time_grid[i]
    for j in range(n_maturities):
        if maturity_grid[j] < t_val:
            f_surface[i, j] = np.nan

surf = ax.plot_surface(t_mesh, T_mesh, f_surface * 100, cmap='viridis', edgecolor='none', alpha=0.85)
ax.set_xlabel('Current Time $t$ (Years)', fontsize=11, labelpad=10)
ax.set_ylabel('Maturity $T$ (Years)', fontsize=11, labelpad=10)
ax.set_zlabel('Forward Rate $f(t,T)$ (%)', fontsize=11, labelpad=10)
ax.set_title('Term Structure Dynamics $f(t,T)$ under HJM SOFR Model', fontsize=13, fontweight='bold', pad=15)
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Forward Rate (%)')
plt.tight_layout()
plt.savefig("figures/fig1_forward_surface.png")
plt.close()

# Figure 2: Compounded SOFR Distribution vs Black-76 Log-Normal Fit
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
n_bins, bins, patches = ax.hist(R_compounded_paths * 100, bins=50, density=True, alpha=0.6, color='#2b5c8f', edgecolor='black', label='Compounded SOFR $R(T_1, T_2)$ MC Distribution')

# Fit log-normal PDF
shape, loc, scale = stats.lognorm.fit(R_compounded_paths * 100, floc=0)
x_pdf = np.linspace(bins[0], bins[-1], 200)
pdf_fitted = stats.lognorm.pdf(x_pdf, shape, loc, scale)
ax.plot(x_pdf, pdf_fitted, 'r-', lw=2.5, label='Analytical Log-Normal Fit')

ax.axvline(K_strike * 100, color='darkred', linestyle='--', lw=2, label=f'Strike K = {K_strike*100:.1f}%')
ax.axvline(F_SOFR_analytical * 100, color='darkgreen', linestyle='-', lw=2, label=f'Forward Rate = {F_SOFR_analytical*100:.2f}%')

ax.set_xlabel('Compounded SOFR Rate $R(T_1, T_2)$ (%)', fontsize=12)
ax.set_ylabel('Probability Density', fontsize=12)
ax.set_title('Empirical Distribution of Compounded Overnight SOFR Rates', fontsize=13, fontweight='bold')
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
plt.tight_layout()
plt.savefig("figures/fig2_sofr_distribution.png")
plt.close()

# Figure 3: Monte Carlo Short Rate Paths & Forward Curve Term Structure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

# Short rate paths
for k in range(30):
    ax1.plot(time_grid, r_all_paths[:, k] * 100, lw=0.8, alpha=0.7)
ax1.plot(time_grid, r_all_paths.mean(axis=1) * 100, 'k-', lw=3, label='Mean Short Rate $E[r(t)]$')
ax1.set_xlabel('Time $t$ (Years)', fontsize=11)
ax1.set_ylabel('Short Rate $r(t)$ (%)', fontsize=11)
ax1.set_title('Simulated Short Rate Trajectories $r(t)$', fontsize=12, fontweight='bold')
ax1.legend(loc='upper right', frameon=True)

# Forward Curve Snapshots
times_to_plot = [0.0, 1.0, 2.0, 3.0]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
for idx_t, t_val in enumerate(times_to_plot):
    step_idx = int(t_val / dt)
    mat_sub = maturity_grid[maturity_grid >= t_val]
    f_sub = f_path[step_idx, maturity_grid >= t_val]
    ax2.plot(mat_sub, f_sub * 100, lw=2.2, color=colors[idx_t], label=f'Forward Curve at $t={t_val:.1f}Y$')

ax2.set_xlabel('Maturity $T$ (Years)', fontsize=11)
ax2.set_ylabel('Forward Rate $f(t, T)$ (%)', fontsize=11)
ax2.set_title('Forward Curve Evolution $f(t, T)$ Across Time', fontsize=12, fontweight='bold')
ax2.legend(loc='upper right', frameon=True)

plt.tight_layout()
plt.savefig("figures/fig3_rate_paths_and_curves.png")
plt.close()

# Save summary numerical data
with open("scratch/numerical_results.txt", "w") as f:
    f.write(f"Initial Short Rate r0: {r0*100:.2f}%\n")
    f.write(f"Analytical Forward SOFR (1Y-2Y): {F_SOFR_analytical*100:.4f}%\n")
    f.write(f"Monte Carlo Forward SOFR (1Y-2Y): {F_SOFR_mc*100:.4f}%\n")
    f.write(f"SOFR Caplet Price (Strike 4.0%): {caplet_price_mc*10000:.2f} bps\n")

print("All numerical simulations completed and figures saved successfully!")

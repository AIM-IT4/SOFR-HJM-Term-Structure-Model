import numpy as np
import scipy.stats as stats

np.random.seed(42)

# Parameters
r0 = 0.038412
r_inf = 0.051772
kappa = 0.4001
gamma = -0.0014
sigma0 = 0.00591
a = 0.25

T1 = 1.0
T2 = 2.0
K = 0.0450
K_star = 1.0 + K * (T2 - T1)

# Analytical Jamshidian Formula
def y(T):
    exp_kT = np.exp(-kappa * T)
    return (r_inf * T + (r0 - r_inf) * (1 - exp_kT) / kappa + gamma * (1 - exp_kT - kappa * T * exp_kT) / kappa**2) / T

P1 = np.exp(-y(T1) * T1)
P2 = np.exp(-y(T2) * T2)

sig_p = (sigma0 / a) * (1.0 - np.exp(-a * (T2 - T1))) * np.sqrt((1.0 - np.exp(-2.0 * a * T1)) / (2.0 * a))
d1 = (np.log(P1 / (K_star * P2)) + 0.5 * sig_p**2) / sig_p
d2 = d1 - sig_p

analytical_caplet = (K_star * P2 * stats.norm.cdf(-d2) - P1 * stats.norm.cdf(-d1)) * 10000
print(f"Exact Jamshidian Analytical Caplet: {analytical_caplet:.4f} bps")

# High-Precision Exact Simulation of (r(T1), P(T1, T2)) under Forward Measure
# Under risk-neutral measure Q:
# Short rate r(t) has exact analytical conditional Gaussian distribution!
# Mean and variance of \int_0^T r(u) du and r(T) are known in closed form.

n_paths = 100000
# Simulate r(T1) directly from exact transition density
var_r1 = (sigma0**2 / (2 * a)) * (1 - np.exp(-2 * a * T1))
std_r1 = np.sqrt(var_r1)

# Exact mean of r(T1) under Q
exp_aT1 = np.exp(-a * T1)
f0_T1 = r0 + (r_inf - r0) * (1 - np.exp(-kappa * T1)) + gamma * T1 * np.exp(-kappa * T1)
mean_r1 = f0_T1 + (sigma0**2 / (2 * a**2)) * (1 - exp_aT1)**2

Z = np.random.normal(0, 1, n_paths)
r1_samples = mean_r1 + std_r1 * Z

# Exact P(T1, T2) given r(T1)
B_T1_T2 = (1.0 - np.exp(-a * (T2 - T1))) / a
A_T1_T2 = (P2 / P1) * np.exp(B_T1_T2 * f0_T1 - (sigma0**2 / (4 * a)) * B_T1_T2**2 * (1 - np.exp(-2 * a * T1)))
P_T1_T2_samples = A_T1_T2 * np.exp(-B_T1_T2 * (r1_samples - f0_T1))

# Discounted Payoff at T1
payoff_T1 = np.maximum(1.0 - K_star * P_T1_T2_samples, 0.0)
mc_caplet_exact = (P1 * payoff_T1).mean() * 10000

print(f"Exact Forward Measure MC Caplet: {mc_caplet_exact:.4f} bps")
print(f"Pricing Difference: {abs(analytical_caplet - mc_caplet_exact):.4f} bps")

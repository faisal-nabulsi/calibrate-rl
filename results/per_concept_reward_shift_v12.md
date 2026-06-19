# per-concept reward shift — v12_completions (2880 rollouts, 90 steps)
early = steps 1-30, late = steps 61-90; reward = correctness (thresholded >=0.5); sorted by delta (decliners first).

| concept | early | late | delta | nE/nL |
|---|--|--|--|--|
| complex_modulus_power | 0.688 | 0.359 | -0.33 DOWN | 16/64 |
| modular_exponent | 0.875 | 0.547 | -0.33 DOWN | 16/64 |
| complement_prob_mn | 0.875 | 0.583 | -0.29 DOWN | 8/24 |
| divisor_sum_filter | 0.854 | 0.562 | -0.29 DOWN | 48/48 |
| triangular_filter_count | 0.578 | 0.403 | -0.17 DOWN | 64/72 |
| constrained_divisor_count | 0.781 | 0.625 | -0.16 DOWN | 32/32 |
| ordered_triple_constraint | 0.458 | 0.375 | -0.08 DOWN | 24/40 |
| count_pythagorean | 0.375 | 0.333 | -0.04 DOWN | 32/24 |
| multi_constraint_square | 0.321 | 0.3 | -0.02 flat | 56/40 |
| polynomial_sign_intervals | 0.312 | 0.321 | +0.01 flat | 48/56 |
| inclusion_exclusion_3set | 0.354 | 0.406 | +0.05 UP | 48/32 |
| lattice_points_circle | 0.562 | 0.625 | +0.06 UP | 16/8 |
| perfect_square_divisible | 0.857 | 0.938 | +0.08 UP | 56/16 |
| complex_eq_solcount | 0.575 | 0.688 | +0.11 UP | 40/16 |
| poly_remainder | 0.4 | 0.521 | +0.12 UP | 40/48 |
| algebraic_system_2eq | 0.75 | 0.875 | +0.12 UP | 24/8 |
| constrained_subset_count | 0.125 | 0.25 | +0.12 UP | 56/24 |
| continued_fraction | 0.375 | 0.5 | +0.12 UP | 56/40 |
| roots_of_unity_sum | 0.325 | 0.45 | +0.12 UP | 40/80 |
| telescoping_mn | 0.229 | 0.375 | +0.15 UP | 48/40 |
| custom_binary_op | 0.344 | 0.5 | +0.16 UP | 32/8 |
| equalization_fraction | 0.625 | 0.812 | +0.19 UP | 24/32 |
| prime_power_divisors | 0.375 | 0.562 | +0.19 UP | 32/16 |
| lcm_gcd_system | 0.475 | 0.679 | +0.20 UP | 40/56 |
| constrained_digit_count | 0.375 | 0.688 | +0.31 UP | 40/32 |
| alternating_cubes | 0.25 | 0.775 | +0.53 UP | 8/40 |
| box_diagonal_sq | 0.5 | None | — | 16/0 |

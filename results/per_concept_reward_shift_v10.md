# per-concept reward shift — training_completions (3840 rollouts, 120 steps)
early = steps 1-40, late = steps 81-120; reward = correctness (thresholded >=0.5); sorted by delta (decliners first).

| concept | early | late | delta | nE/nL |
|---|--|--|--|--|
| multi_constraint_square | 0.3 | 0.225 | -0.07 DOWN | 40/40 |
| triangular_filter_count | 0.542 | 0.486 | -0.06 DOWN | 72/72 |
| polynomial_sign_intervals | 0.438 | 0.417 | -0.02 flat | 16/24 |
| divisor_sum_filter | 0.906 | 0.9 | -0.01 flat | 32/40 |
| equalization_fraction | 0.656 | 0.675 | +0.02 flat | 64/40 |
| modular_exponent | 0.25 | 0.292 | +0.04 UP | 40/48 |
| roots_of_unity_sum | 0.545 | 0.602 | +0.06 UP | 88/88 |
| prime_power_divisors | 0.25 | 0.312 | +0.06 UP | 8/16 |
| algebraic_system_2eq | 0.484 | 0.562 | +0.08 UP | 64/64 |
| constrained_digit_count | 0.325 | 0.425 | +0.10 UP | 40/40 |
| lcm_gcd_system | 0.448 | 0.552 | +0.10 UP | 96/96 |
| telescoping_mn | 0.525 | 0.667 | +0.14 UP | 40/24 |
| constrained_divisor_count | 0.375 | 0.531 | +0.16 UP | 24/32 |
| lattice_points_circle | 0.578 | 0.75 | +0.17 UP | 64/64 |
| constrained_subset_count | 0.438 | 0.625 | +0.19 UP | 16/8 |
| complement_prob_mn | 0.812 | 1.0 | +0.19 UP | 16/16 |
| complex_modulus_power | 0.25 | 0.438 | +0.19 UP | 32/32 |
| continued_fraction | 0.536 | 0.732 | +0.20 UP | 56/56 |
| complex_eq_solcount | 0.597 | 0.797 | +0.20 UP | 144/128 |
| box_diagonal_sq | 0.516 | 0.766 | +0.25 UP | 64/64 |
| count_pythagorean | 0.375 | 0.625 | +0.25 UP | 48/56 |
| inclusion_exclusion_3set | 0.417 | 0.667 | +0.25 UP | 24/24 |
| perfect_square_divisible | 0.625 | 0.875 | +0.25 UP | 16/16 |
| ordered_triple_constraint | 0.357 | 0.609 | +0.25 UP | 56/64 |
| poly_remainder | 0.25 | 0.542 | +0.29 UP | 24/24 |
| alternating_cubes | 0.479 | 0.846 | +0.37 UP | 96/104 |

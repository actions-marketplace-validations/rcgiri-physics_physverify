# API overview

The functions most specs need. Each has a docstring with the details: `help(physverify.studies.reference_study)` and so on.

## Building checks

| Name | What it does |
|---|---|
| `Check(family, label, run, budget_s=None)` | One runnable check; `run()` returns a `Result`. |
| `Result(status, message)` | `.ok` (PASS or EXACT), `.failed` (FAIL, ERROR or INCONCLUSIVE). |
| `OrderResult` | A `Result` with `expected`, `fitted`, `hs` and `errors`. |
| `requires("pkg")`, `SkipCheck` | Report SKIP when an optional package is missing. |
| `ode_checks(label, integrate, ...)` | The standard bundle for an ODE solver. |

## Order studies (`physverify`, `physverify.studies`, `physverify.mms`)

| Name | What it does |
|---|---|
| `ManufacturedODE(u, rhs_ref)` | A manufactured solution and its source term. |
| `mms_order_study(integrate, mms, t_end, ns, order)` | Error at `t_end` against the manufactured solution. |
| `mms_trajectory_study(...)` | Largest error over the whole run. |
| `backward_mms_study(...)` | The same, integrating from `t_end` back to 0. |
| `reference_study(integrate, rhs_ref, y0, t_end, ns, order)` | Against a fine RK4 reference. |
| `invariant_study(integrate, quantity, y0, t_end, ns, order)` | Drift of a conserved quantity. |
| `patch_study(integrate, rhs_ref, y0, slope, t_end, ns)` | A linear solution reproduced to round-off. |
| `trajectory_order_study(runs, exact, t_compare, order, period=None)` | From whole trajectories, at one fixed time. |
| `check_order(hs, errors, expected)` | The verdict from step sizes and errors. |
| `check_exact(hs, errors)` | The verdict when every error should be at round-off. |

## Other checks (`physverify.studies`)

| Name | What it does |
|---|---|
| `balance_check(measure, expected, resolutions)` | An exact budget at every resolution. |
| `time_grid_check(times_of_run, t_start, t_stop, ns)` | The run ends at `t_stop` after exactly n steps. |
| `size_sweep_check(run_at_size, sizes)` | The code runs for odd and even sizes. |
| `coverage_check(simulate, interval, prior_sampler, level=...)` | Coverage of stated intervals. |
| `damped_sinusoid_fit(t, y, t_start, t_stop)` | Complex frequency of a ringdown. |

## Runge-Kutta tables (`physverify.butcher`)

`check_tableau`, `tableau_order`, `order_residuals`, `linear_order`, `stage_order`, `stability_function`, `stability_polynomials`, `r_infinity`, `a_stability_margin`, `is_stiffly_accurate`. See [Runge-Kutta tables](checks/runge-kutta.md).

## Loading code (`physverify.loaders`)

| Name | What it does |
|---|---|
| `load_module_from_path(path, stubs=None)` | Import a file as a module. |
| `load_definitions_from_path(path, stubs=None)` | Only its functions and classes, without running the script. |
| `run_script(path, argv=(), inputs=None)` | Run a whole script; returns (globals, printed text). |
| `stub_modules({...})` | Stand-ins for imports the tested code does not use. |

## Exact references (`physverify.references`)

Listed by `physverify references`; see [Exact references](checks/exact-references.md).

## Reports (`physverify.report`)

`run_checks(checks, budget_s=None)`, `to_text`, `to_json`, `to_markdown`, `to_html`, `summary`.

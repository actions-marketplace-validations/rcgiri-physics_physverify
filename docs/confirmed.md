# Confirmed by maintainers

While physverify was tested on public physics code, each suspected defect was checked by a run against a reference from the physics and reported to the project. These are reports where the project's maintainers confirmed the defect or merged a fix (checked 2026-11-21). Some were settled with physverify itself, others with a standalone convergence test in the project's own language. The link in each row is the source; the one-line summaries are ours.

### Time integration

| Project | Report | What was found | Maintainer response or fix |
|---|---|---|---|
| OrdinaryDiffEq.jl | [#5001](https://github.com/SciML/OrdinaryDiffEq.jl/issues/5001) | `constructFeagin12`: one node stored as 2 instead of 0.2, so the 12th-order method converges at first order on time-dependent problems | [confirmed](https://github.com/SciML/OrdinaryDiffEq.jl/issues/5001#issuecomment-6912646149); fixed in [PR #5002](https://github.com/SciML/OrdinaryDiffEq.jl/pull/5002) |
| SUNDIALS (ARKODE) | [#1083](https://github.com/llnl/sundials/issues/1083) | `SPRKStep`: each right-hand side gets the time of the variable it updates, not of the one it reads, so a time-dependent force makes every symplectic table first order | [reproduced, with a proposed fix](https://github.com/llnl/sundials/issues/1083#issuecomment-7022495963); a second item in the report was not a bug (it came from the argument order) |
| Hipparchus | [#507](https://github.com/Hipparchus-Math/hipparchus/issues/507) | `AdamsMoultonIntegrator`: the documentation says a k-step method has order k+1, but it converges at order k | [confirmed](https://github.com/Hipparchus-Math/hipparchus/issues/507#issuecomment-7034818960); documentation fix and regression test planned for 5.0 |
| qmat | [#23](https://github.com/Parallel-in-Time/qmat/issues/23) | three Runge-Kutta schemes labelled with a higher order than they have | [confirmed](https://github.com/Parallel-in-Time/qmat/issues/23#issuecomment-6285619780); fixed in [PR #24](https://github.com/Parallel-in-Time/qmat/pull/24), and qmat now checks its tables with `physverify.butcher` in its tests |
| qmat | [#25](https://github.com/Parallel-in-Time/qmat/issues/25) | RK21: weights differ from the cited Wang and Spiteri NSSP(2,1) | [confirmed](https://github.com/Parallel-in-Time/qmat/issues/25#issuecomment-6962036618) (a leftover from experiments); fixed |
| jaxfun | [#71](https://github.com/spectralDNS/jaxfun/issues/71) | IMEX-SSP2(2,2,2): the implicit table differs from Pareschi and Russo, so the scheme is first order | [confirmed, fix in progress](https://github.com/spectralDNS/jaxfun/issues/71#issuecomment-7016522090) |

### Units and physical constants

| Project | Report | What was found | Maintainer response or fix |
|---|---|---|---|
| SymPy | [#30810](https://github.com/sympy/sympy/issues/30810) | `units`: the astronomical unit, nautical mile and torr differ from their exact definitions | [confirmed by a core developer against primary sources](https://github.com/sympy/sympy/issues/30810#issuecomment-6400981470) |
| Astropy | [#20681](https://github.com/astropy/astropy/issues/20681) | the "surface tension" physical type is registered as J m² instead of J/m² | [confirmed by a maintainer](https://github.com/astropy/astropy/issues/20681#issuecomment-6458904156); issue open |
| PyAstronomy | [#71](https://github.com/sczesla/PyAstronomy/issues/71) | `pyasl.planck` used CGS constants where SI were expected; the cause was wider: the two constants modules (with and without `quantities`) defaulted to different unit systems | [confirmed and fixed](https://github.com/sczesla/PyAstronomy/issues/71#issuecomment-6509866771) |
| TESPy | [#1127](https://github.com/oemof/tespy/issues/1127) | the pressure term of the incompressible-fluid entropy has the wrong units | [confirmed; fixed in dev](https://github.com/oemof/tespy/issues/1127#issuecomment-6857850733) |

### Other physics and numerical code

| Project | Report | What was found | Maintainer response or fix |
|---|---|---|---|
| EinsteinPy | [#705](https://github.com/einsteinpy/einsteinpy/issues/705) | `DeSitter()` puts the scale factor on a spatial coordinate | fixed in [PR #707](https://github.com/einsteinpy/einsteinpy/pull/707) |
| findiff | [#119](https://github.com/maroba/findiff/issues/119) | `set_accuracy` is ignored after the first call | fixed in [038c34f](https://github.com/maroba/findiff/commit/038c34f95a847d65dd678ad28b47d8b184bc2fc5) |
| findiff | [#120](https://github.com/maroba/findiff/issues/120) | `3 - Diff(0)` has the wrong sign | fixed in [3443729](https://github.com/maroba/findiff/commit/344372940b7993d5e4b5944e2c15db93e68d0c0d) |
| openmmtools | [#822](https://github.com/choderalab/openmmtools/issues/822) | the harmonic-oscillator test system reports the wrong standard deviation of its potential | [confirmed by a developer](https://github.com/choderalab/openmmtools/issues/822#issuecomment-6473317809) |
| Pynite | [#353](https://github.com/JWock82/Pynite/issues/353) | `BeamSegY.max_moment` ignores `P_delta` | [confirmed by the author; fix planned](https://github.com/JWock82/Pynite/issues/353#issuecomment-6786729418) |

### Software defects found along the way

| Project | Report | What was found | Maintainer response or fix |
|---|---|---|---|
| PyGMT | [#4960](https://github.com/GenericMappingTools/pygmt/issues/4960) | `sequence_join` treats any string containing a space as a datetime | [discussed](https://github.com/GenericMappingTools/pygmt/issues/4960#issuecomment-6408232132); fixed in [PR #4961](https://github.com/GenericMappingTools/pygmt/pull/4961) |
| moltemplate | [#120](https://github.com/jewettaij/moltemplate/issues/120) | `msifrc2lt.py`: an undefined name in the out-of-plane branch | [confirmed by the author](https://github.com/jewettaij/moltemplate/issues/120#issuecomment-6737460886); fix merged |

Smaller projects whose authors fixed a reported defect include [freepaths](https://github.com/anufrievroman/freepaths/issues/31), [ugropy](https://github.com/ipqa-research/ugropy/issues/46), [phlower](https://github.com/ricosjp/phlower/issues/2), [spin-model-transformers](https://github.com/mcbal/spin-model-transformers/issues/2), [finitevolume2-python](https://github.com/pmocz/finitevolume2-python/issues/3), [mhd-boris](https://github.com/pmocz/mhd-boris/issues/2) and [StatMech_IsingModel](https://github.com/PHYS3934/StatMech_IsingModel/issues/4).

This list shows that the defects were real; it is not a measure of how often physverify finds bugs. The time-integration defects come from the [Runge–Kutta table census](census.md). Most of the others were found by a test script written for each repository, with physverify running the checks and the sandbox (see [Results on real code](results.md)).

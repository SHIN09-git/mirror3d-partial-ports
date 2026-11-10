# Pure retroreflection in a finite mirror lattice

The proof starts with a fixed matching of the six directions at each lattice site. The transverse directions are periodic and the two ends of the longitudinal axis are open. The right face is divided into counted outlets $A$ and a set $W$ that will retroreflect. The result holds for every matching environment and every Boolean mask, including empty and full masks. [Paper, model and reduction](../paper/main.tex#L87-L125) · [Supplement, microscopic geometry](../paper/sm.tex#L22-L49)

For every left source, the open model and the retroreflecting model use the same local scattering and link steps. A ray reaching $A$ follows the same trace. A ray reaching $W$ follows its open trace and then encounters the same mirrors in reverse order, entering each through its former outgoing port. Consequently,

$$
C_{\rm retro}=n_{LA}^{\rm open},\qquad
f_L=n_{LW}^{\rm open},\qquad
N=C_{\rm retro}+f_L.
$$

Here $N$ counts all left-to-right paths with the right face open and $f_L$ counts left ports whose ray returns to that very port. For each observed terminal $\alpha$, the proof also gives the port budget

$$
2n_{\alpha\alpha}+\sum_{\beta\ne\alpha}n_{\alpha\beta}+f_\alpha=A_\alpha.
$$

An ordinary return is counted as an unordered pair of distinct ports on the same terminal. Each such pair has exactly two starting ports. A fixed return has exactly one.

| Proof | Lean entry points |
| --- | --- |
| Local tracing, termination at a boundary, and periodic interior orbits | [`Trace.terminal_unique`, `Trace.open_distinct`, `open_path_or_cycle`](MirrorPorts/Trace.lean) |
| Unchanged paths and the complete reversed sequence of mirror encounters | [`kept_path`, `retraced_path`, `retro_fixed_iff`](MirrorPorts/Reflection.lean) |
| Three count identities and terminal port budgets | [`pure_retroreflection_counts`, `terminal_port_identity`](MirrorPorts/Counts.lean) |
| Cubic geometry with explicit nearest-neighbour wires and periodic seams | [`boundary_eq_faces`, `cubic_reduction`](MirrorPorts/Slab.lean) |
| A $2\times2\times1$ slab with two straight lanes, one counted outlet and one reflector | [`two_lane_paths`, `two_lane_counts`](MirrorPorts/Example.lean) |

In the two-lane example the proof checks the individual mirror encounters and obtains $N=2$, $C_{\rm retro}=1$ and $f_L=1$. The finite-graph theorems apply to individual environments for both matching rules in the paper. Statistical extrapolation, continuum predictions and the execution of the Python sampler are outside the proof.

## Reproduce

With the Lean toolchain manager installed, run from this directory

```sh
lake exe cache get Mathlib.Dynamics.PeriodicPts.Lemmas Mathlib.Algebra.BigOperators.Group.Finset.Basic Mathlib.Algebra.Group.Fin.Basic Mathlib.Data.Fintype.Prod Mathlib.Tactic.DeriveFintype
lake build
lake env lean -DwarningAsError=true Audit.lean
```

Lean 4.24.0 and mathlib are pinned in [lean-toolchain](lean-toolchain) and [lake-manifest.json](lake-manifest.json). The [axiom audit](Audit.lean) checks every project declaration against `propext`, `Classical.choice` and `Quot.sound`. The [GitHub workflow](../.github/workflows/lean.yml) also uses the pinned official checker to replay `MirrorPorts.Example` and all its imports in a fresh kernel.

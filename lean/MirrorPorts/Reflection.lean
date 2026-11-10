import MirrorPorts.Trace

/-! Change the boundary rule, retaining the same local mirrors and wires. -/

namespace MirrorPorts.Network

variable {P : Type*} (g : Network P)

/-- A detector absorbs on arrival. All unobserved exterior ports send the ray
back along its incident link, using the same wire and the same mirrors. -/
structure Detectors (g : Network P) where
  ports : Set P
  exterior : ports ⊆ g.boundary

def full : Detectors g := ⟨g.boundary, Set.Subset.rfl⟩

def retro (W : Set P) : Detectors g := ⟨g.boundary \ W, fun _ h => h.1⟩

variable {g}

namespace Detectors

variable [Finite P] (d : Detectors g)

/-- The unique detected endpoint. Off the detector set we extend by the identity. -/
noncomputable def endpoint (x : P) : P := by
  classical
  exact if hx : x ∈ d.ports then (g.reaches_terminal d.exterior hx).choose else x

theorem endpoint_trace {x : P} (hx : x ∈ d.ports) :
    ∃ xs, g.Trace d.ports x xs (d.endpoint x) ∧ d.endpoint x ∈ d.ports := by
  classical
  unfold endpoint
  rw [dif_pos hx]
  exact (g.reaches_terminal d.exterior hx).choose_spec

theorem endpoint_eq_of_trace {x y : P} {xs : List P}
    (hx : x ∈ d.ports) (p : g.Trace d.ports x xs y) (hy : y ∈ d.ports) :
    d.endpoint x = y := by
  obtain ⟨_, t, ht⟩ := d.endpoint_trace hx
  exact (t.terminal_unique ht p hy).2

theorem endpoint_involutive : Function.Involutive d.endpoint := by
  intro x
  by_cases hx : x ∈ d.ports
  · obtain ⟨_, t, ht⟩ := d.endpoint_trace hx
    exact d.endpoint_eq_of_trace ht (t.reversed d.exterior) hx
  · have he : d.endpoint x = x := by simp [endpoint, hx]
    rw [he, he]

end Detectors

variable (g)

theorem full_endpoint_ne [Finite P] {x : P} (hx : x ∈ g.boundary) :
    g.full.endpoint x ≠ x := by
  obtain ⟨_, t, _⟩ := g.full.endpoint_trace hx
  exact t.open_distinct

/-- An open trace ending on W is followed by the same mirror encounters in
reverse order, with incoming and outgoing halves exchanged at each mirror. -/
theorem retraced_path {x y : P} {xs : List P} (W : Set P)
    (p : g.Trace g.boundary x xs y) (hy : y ∈ g.boundary) (hw : y ∈ W) :
    g.Trace (g.retro W).ports x (xs ++ g.backwards xs) x := by
  have fwd := p.weaken (g.retro W).exterior
  have rev := fwd.reversed (g.retro W).exterior
  have he : g.wire y = y := hy
  exact fwd.append (fun h => h.2 hw) (he.symm ▸ rev)

/-- A still-open endpoint has exactly the original trace. -/
theorem kept_path {x y : P} {xs : List P} (W : Set P)
    (p : g.Trace g.boundary x xs y) (hy : y ∈ g.boundary) (hw : y ∉ W) :
    g.Trace (g.retro W).ports x xs y ∧ y ∈ (g.retro W).ports :=
  ⟨p.weaken (g.retro W).exterior, hy, hw⟩

theorem retro_hits_wall [Finite P] {W : Set P} {x : P} (hx : x ∈ (g.retro W).ports)
    (hw : g.full.endpoint x ∈ W) : (g.retro W).endpoint x = x := by
  obtain ⟨_, t, ht⟩ := g.full.endpoint_trace (g.retro W |>.exterior hx)
  exact (g.retro W).endpoint_eq_of_trace hx (g.retraced_path W t ht hw) hx

theorem retro_misses_wall [Finite P] {W : Set P} {x : P} (hx : x ∈ (g.retro W).ports)
    (hw : g.full.endpoint x ∉ W) : (g.retro W).endpoint x = g.full.endpoint x := by
  obtain ⟨_, t, ht⟩ := g.full.endpoint_trace (g.retro W |>.exterior hx)
  obtain ⟨p, hy⟩ := g.kept_path W t ht hw
  exact (g.retro W).endpoint_eq_of_trace hx p hy

theorem retro_fixed_iff [Finite P] {W : Set P} {x : P} (hx : x ∈ (g.retro W).ports) :
    (g.retro W).endpoint x = x ↔ g.full.endpoint x ∈ W := by
  constructor
  · intro h
    by_contra hw
    rw [g.retro_misses_wall hx hw] at h
    exact g.full_endpoint_ne ((g.retro W).exterior hx) h
  · exact g.retro_hits_wall hx

end MirrorPorts.Network

import Mathlib.Dynamics.PeriodicPts.Lemmas

/-! Finite mirror traces, built one local scattering event at a time. -/

namespace MirrorPorts

open Function

/-- A port is an incident half-edge. The mirror pairs halves at a vertex.
The wire pairs halves of a link and fixes exterior ports. -/
structure Network (P : Type*) where
  mirror : P → P
  mirror_inv : Involutive mirror
  mirror_ne : ∀ p, mirror p ≠ p
  wire : P → P
  wire_inv : Involutive wire

namespace Network

variable {P : Type*} (g : Network P)

def boundary : Set P := {p | g.wire p = p}

def step (p : P) : P := g.wire (g.mirror p)

theorem step_injective : Injective g.step := g.wire_inv.injective.comp g.mirror_inv.injective

/-- The list records incoming ports, one per mirror encounter. An exterior wire
which is allowed to continue feeds the outgoing port back in as the next input. -/
inductive Trace (stops : Set P) : P → List P → P → Prop
  | one (x : P) : Trace stops x [x] (g.mirror x)
  | more {x y : P} {xs : List P} (go : g.mirror x ∉ stops)
      (tail : Trace stops (g.step x) xs y) : Trace stops x (x :: xs) y

/-- Incoming ports when traversing the same mirror pairs in reverse order. -/
def backwards (xs : List P) : List P := xs.reverse.map g.mirror

variable {g} {B B' : Set P} {x y z : P} {xs ys : List P}

theorem mem_wire_iff (hb : B ⊆ g.boundary) (q : P) : g.wire q ∈ B ↔ q ∈ B := by
  constructor
  · intro h
    have he : g.wire (g.wire q) = g.wire q := hb h
    rw [g.wire_inv] at he
    rwa [he]
  · intro h
    have he : g.wire q = q := hb h
    rwa [he]

namespace Trace

theorem cases_head (p : g.Trace B x xs y) :
    (xs = [x] ∧ y = g.mirror x) ∨
      ∃ tail, xs = x :: tail ∧ g.mirror x ∉ B ∧ g.Trace B (g.step x) tail y := by
  cases p with
  | one => exact Or.inl ⟨rfl, rfl⟩
  | more h t => exact Or.inr ⟨_, rfl, h, t⟩

theorem weaken (p : g.Trace B x xs y) (h : B' ⊆ B) : g.Trace B' x xs y := by
  induction p with
  | one x => exact .one x
  | more go _ ih => exact .more (fun hx => go (h hx)) ih

theorem append (p : g.Trace B x xs y) (go : y ∉ B) (q : g.Trace B (g.wire y) ys z) :
    g.Trace B x (xs ++ ys) z := by
  induction p with
  | one x => exact .more go q
  | more h _ ih => exact .more h (ih go q)

theorem reversed (p : g.Trace B x xs y) (hb : B ⊆ g.boundary) :
    g.Trace B y (g.backwards xs) x := by
  induction p with
  | one x =>
    simpa [backwards, g.mirror_inv x] using (Trace.one (g := g) (stops := B) (g.mirror x))
  | @more x y xs go _ ih =>
    have last : g.Trace B (g.wire (g.step x)) [g.mirror x] x := by
      simpa [step, g.wire_inv (g.mirror x), g.mirror_inv x] using
        (Trace.one (g := g) (stops := B) (g.mirror x))
    have pass : g.step x ∉ B := fun h => go ((mem_wire_iff hb _).mp h)
    simpa [backwards] using ih.append pass last

/-- From one source, two traces run to absorption agree at every encounter. -/
theorem terminal_unique (p : g.Trace B x xs y) (hy : y ∈ B)
    (q : g.Trace B x ys z) (hz : z ∈ B) : xs = ys ∧ y = z := by
  induction p generalizing ys z with
  | one x =>
    rcases q.cases_head with ⟨rfl, rfl⟩ | ⟨_, _, h, _⟩
    · exact ⟨rfl, rfl⟩
    · exact (h hy).elim
  | @more x y xs go _ ih =>
    rcases q.cases_head with ⟨_, rfl⟩ | ⟨tail, rfl, _, ht⟩
    · exact (go hz).elim
    · obtain ⟨rfl, rfl⟩ := ih hy ht hz
      exact ⟨rfl, rfl⟩

/-- After the recorded encounters the next input is the wire at the last output. -/
theorem iterate_length (p : g.Trace B x xs y) : g.step^[xs.length] x = g.wire y := by
  induction p with
  | one => rfl
  | more _ _ ih => exact ih

private theorem suffix_from (p : g.Trace B x xs y) {q : P} (hq : q ∈ xs) :
    ∃ rest, g.Trace B q rest y ∧ rest.length ≤ xs.length := by
  induction p with
  | one x =>
    have he : q = x := List.mem_singleton.mp hq
    subst q
    exact ⟨_, .one x, le_rfl⟩
  | more go t ih =>
    rcases List.mem_cons.mp hq with rfl | h
    · exact ⟨_, .more go t, le_rfl⟩
    · obtain ⟨rest, tr, hl⟩ := ih h
      exact ⟨rest, tr, hl.trans (Nat.le_succ _)⟩

/-- A trace that reaches a detector never repeats an incoming port. -/
theorem nodup_of_terminal (p : g.Trace B x xs y) (hy : y ∈ B) : xs.Nodup := by
  induction p with
  | one => simp
  | more go t ih =>
    refine List.nodup_cons.mpr ⟨?_, ih hy⟩
    intro hx
    obtain ⟨rest, tr, hl⟩ := t.suffix_from hx
    have he := congrArg List.length (((Trace.more go t).terminal_unique hy tr hy).1)
    simp only [List.length_cons] at he
    omega

theorem length_le_ports [Fintype P] (p : g.Trace B x xs y) (hy : y ∈ B) :
    xs.length ≤ Fintype.card P := (p.nodup_of_terminal hy).length_le_card

/-- Strip the first mirror pair, then reverse the rest and strip the last.
A self-return would leave a fixed mirror or an unabsorbed fixed wire at its centre. -/
theorem open_distinct (p : g.Trace g.boundary x xs y) : y ≠ x := by
  induction hlen : xs.length using Nat.strong_induction_on generalizing x xs y with
  | h n ih =>
    intro hxy
    subst y
    rcases p.cases_head with ⟨_, he⟩ | ⟨tail, rfl, go, ht⟩
    · exact g.mirror_ne x he.symm
    · rcases (ht.reversed (Set.Subset.rfl)).cases_head with ⟨_, he⟩ | ⟨inner, hi, _, hp⟩
      · exact go he
      · have hsize := congrArg List.length hi
        simp [backwards] at hsize
        simp at hlen
        exact (ih inner.length (by omega) hp rfl) rfl

end Trace

variable (g)

/-- Finiteness is used only for recurrence of the reversible local step. -/
theorem step_period [Finite P] (x : P) : ∃ n, 0 < n ∧ g.step^[n] x = x := by
  obtain ⟨n, hn, hp⟩ := g.step_injective.mem_periodicPts x
  exact ⟨n, hn, hp⟩

/-- If a positive iterate is absorbing, the trace ends at the first absorbing port. -/
theorem reaches_of_iterate (hb : B ⊆ g.boundary) (n : ℕ) (x : P)
    (h : g.step^[n + 1] x ∈ B) : ∃ y xs, g.Trace B x xs y ∧ y ∈ B := by
  induction n generalizing x with
  | zero =>
    exact ⟨_, _, .one x, (mem_wire_iff hb _).mp h⟩
  | succ n ih =>
    by_cases stop : g.mirror x ∈ B
    · exact ⟨_, _, .one x, stop⟩
    · obtain ⟨y, xs, p, hy⟩ := ih (g.step x) h
      exact ⟨y, x :: xs, .more stop p, hy⟩

theorem reaches_terminal [Finite P] (hb : B ⊆ g.boundary) (hx : x ∈ B) :
    ∃ y xs, g.Trace B x xs y ∧ y ∈ B := by
  obtain ⟨n, hn, h⟩ := g.step_period x
  cases n with
  | zero => exact (Nat.lt_irrefl 0 hn).elim
  | succ n => exact g.reaches_of_iterate hb n x (h.symm ▸ hx)

/-- A completed open trace and an all-interior orbit are mutually exclusive. -/
theorem open_trace_hits_boundary {xs : List P} {x y : P}
    (p : g.Trace g.boundary x xs y) (hy : y ∈ g.boundary) :
    g.step^[xs.length] x ∈ g.boundary := by
  rw [p.iterate_length, (show g.wire y = y from hy)]
  exact hy

/-- Every starting port leads to the exterior or belongs to a periodic interior orbit. -/
theorem open_path_or_cycle [Finite P] (x : P) :
    (∃ y xs, g.Trace g.boundary x xs y ∧ y ∈ g.boundary) ∨
    ((∃ n, 0 < n ∧ g.step^[n] x = x) ∧ ∀ n, g.step^[n] x ∉ g.boundary) := by
  by_cases h : ∃ n, g.step^[n] x ∈ g.boundary
  · obtain ⟨n, hn⟩ := h
    cases n with
    | zero => exact Or.inl (g.reaches_terminal Set.Subset.rfl hn)
    | succ n => exact Or.inl (g.reaches_of_iterate Set.Subset.rfl n x hn)
  · exact Or.inr ⟨g.step_period x, fun n hn => h ⟨n, hn⟩⟩

end Network
end MirrorPorts

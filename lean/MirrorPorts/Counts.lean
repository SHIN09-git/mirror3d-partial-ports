import MirrorPorts.Reflection
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-! Counts of crossings, two-ended returns, and one-ended fixed returns. -/

namespace MirrorPorts

variable {P : Type*}

private noncomputable def selected (s : Finset P) (p : P → Prop) : Finset P := by
  classical
  exact s.filter p

@[simp] private theorem mem_selected {s : Finset P} {p : P → Prop} {x : P} :
    x ∈ selected s p ↔ x ∈ s ∧ p x := by
  classical
  exact Finset.mem_filter

private noncomputable def tally (s : Finset P) (p : P → Prop) : ℕ := (selected s p).card

private theorem tally_filter (s : Finset P) (p : P → Prop) [DecidablePred p] :
    tally s p = (s.filter p).card := by
  apply congrArg Finset.card
  ext x
  simp only [mem_selected, Finset.mem_filter]

private theorem tally_congr {s : Finset P} {p q : P → Prop}
    (h : ∀ x ∈ s, p x ↔ q x) : tally s p = tally s q := by
  classical
  apply congrArg Finset.card
  ext x
  simp only [mem_selected]
  exact and_congr_right (h x)

private theorem tally_or (s : Finset P) (p q : P → Prop)
    (h : ∀ x ∈ s, p x → ¬q x) :
    tally s (fun x => p x ∨ q x) = tally s p + tally s q := by
  classical
  have hu : selected s (fun x => p x ∨ q x) = selected s p ∪ selected s q := by
    ext x
    simp only [mem_selected, Finset.mem_union]
    grind
  have hd : Disjoint (selected s p) (selected s q) := by
    refine Finset.disjoint_left.mpr (fun {x} hp hq => ?_)
    exact h x (mem_selected.mp hp).1 (mem_selected.mp hp).2 (mem_selected.mp hq).2
  unfold tally
  rw [hu, Finset.card_union_of_disjoint hd]

namespace Network

variable {g : Network P}

namespace Detectors

variable (d : Detectors g)

section
variable [Finite P]

/-- Number of source ports whose traced endpoint belongs to the target. -/
noncomputable def crossings (s : Finset P) (target : Set P) : ℕ :=
  tally s (fun x => d.endpoint x ∈ target)

theorem crossings_eq_card (s : Finset P) (target : Set P)
    [DecidablePred (fun x => d.endpoint x ∈ target)] :
    d.crossings s target = (s.filter (fun x => d.endpoint x ∈ target)).card :=
  tally_filter s _

noncomputable def fixedReturns (s : Finset P) : ℕ := tally s (fun x => d.endpoint x = x)

/-- Count unordered pairs of distinct terminal ports joined by a return path. -/
noncomputable def pairedReturns (s : Finset P) : ℕ := by
  classical
  exact ((selected s fun x => d.endpoint x ∈ s ∧ d.endpoint x ≠ x).image
    (fun x => ({x, d.endpoint x} : Finset P))).card

private theorem paired_ends (s : Finset P) :
    tally s (fun x => d.endpoint x ∈ s ∧ d.endpoint x ≠ x) = 2 * d.pairedReturns s := by
  classical
  let ends := selected s fun x => d.endpoint x ∈ s ∧ d.endpoint x ≠ x
  let pair := fun x => ({x, d.endpoint x} : Finset P)
  change ends.card = 2 * (ends.image pair).card
  rw [Finset.card_eq_sum_card_image pair ends]
  calc
    _ = ∑ _t ∈ ends.image pair, 2 := by
      apply Finset.sum_congr rfl
      intro t ht
      obtain ⟨x, hx, rfl⟩ := Finset.mem_image.mp ht
      obtain ⟨hxs, hfs, hne⟩ := mem_selected.mp hx
      have hii := d.endpoint_involutive x
      have hs : ends.filter (fun p => pair p = pair x) = pair x := by
        ext p
        constructor
        · intro hp
          have he := (Finset.mem_filter.mp hp).2
          have hm : p ∈ pair p := by simp [pair]
          rwa [he] at hm
        · intro hp
          change p ∈ ({x, d.endpoint x} : Finset P) at hp
          simp only [Finset.mem_insert, Finset.mem_singleton] at hp
          rcases hp with rfl | rfl
          · exact Finset.mem_filter.mpr ⟨hx, rfl⟩
          · refine Finset.mem_filter.mpr ⟨mem_selected.mpr ⟨hfs, ?_, ?_⟩, ?_⟩
            · rwa [hii]
            · rw [hii]
              exact hne.symm
            · simp only [pair, hii, Finset.pair_comm (d.endpoint x) x]
      rw [hs]
      exact Finset.card_pair hne.symm
    _ = _ := by simp [Nat.mul_comm]

/-- An ordinary return uses two ports, a crossing or a fixed return uses one. -/
theorem port_balance (s : Finset P) :
    2 * d.pairedReturns s + d.crossings s (s : Set P)ᶜ + d.fixedReturns s = s.card := by
  classical
  have hsplit := tally_or s (fun x => d.endpoint x ∈ s ∧ d.endpoint x ≠ x)
    (fun x => d.endpoint x ∉ s ∨ d.endpoint x = x) (by grind)
  have hsingle := tally_or s (fun x => d.endpoint x ∉ s) (fun x => d.endpoint x = x)
    (by intro x hx hout he; rw [he] at hout; exact hout hx)
  have hall : tally s (fun x => (d.endpoint x ∈ s ∧ d.endpoint x ≠ x) ∨
      (d.endpoint x ∉ s ∨ d.endpoint x = x)) = s.card := by
    apply congrArg Finset.card
    ext x
    simp only [mem_selected]
    grind
  change 2 * d.pairedReturns s + tally s (fun x => d.endpoint x ∉ s) +
      tally s (fun x => d.endpoint x = x) = s.card
  rw [hsplit, hsingle] at hall
  rw [← d.paired_ends, Nat.add_assoc]
  exact hall

end

/-- Detected ports bearing a given terminal label. -/
noncomputable def terminalPorts [Fintype P] {ι : Type*} (label : P → ι) (a : ι) : Finset P :=
  selected Finset.univ (fun x => x ∈ d.ports ∧ label x = a)

@[simp] theorem mem_terminalPorts [Fintype P] {ι : Type*} {label : P → ι} {a : ι} {x : P} :
    x ∈ d.terminalPorts label a ↔ x ∈ d.ports ∧ label x = a := by
  simp [terminalPorts]

/-- The port budget with the cross-terminal contribution summed label by label. -/
theorem terminal_port_identity [Fintype P] {ι : Type*} [Fintype ι] [DecidableEq ι]
    (label : P → ι) (a : ι) :
    let s := d.terminalPorts label a
    2 * d.pairedReturns s + (∑ b ∈ Finset.univ.erase a, d.crossings s {p | label p = b}) +
      d.fixedReturns s = s.card := by
  classical
  let s := d.terminalPorts label a
  let dest := fun p => label (d.endpoint p)
  let others := Finset.univ.erase a

  have hsum : (∑ b ∈ others, d.crossings s {p | label p = b}) = d.crossings s (s : Set P)ᶜ := by
    calc
      _ = ∑ b ∈ others, (s.filter (fun x => dest x = b)).card :=
        Finset.sum_congr rfl (fun b _ => tally_filter s (fun x => dest x = b))
      _ = (s.filter (fun x => dest x ∈ others)).card :=
        Finset.sum_card_fiberwise_eq_card_filter s others dest
      _ = tally s (fun x => dest x ∈ others) := (tally_filter s _).symm
      _ = _ := by
        apply tally_congr
        intro x hx
        obtain ⟨_, _, hy⟩ := d.endpoint_trace ((d.mem_terminalPorts.mp hx).1)
        change label (d.endpoint x) ∈ Finset.univ.erase a ↔ d.endpoint x ∉ d.terminalPorts label a
        simp [hy]
  change 2 * d.pairedReturns s + (∑ b ∈ others, d.crossings s {p | label p = b}) +
      d.fixedReturns s = s.card
  rw [hsum]
  exact d.port_balance s

end Detectors

variable (g) [Finite P]

/-- The three pathwise count identities of the paper. The whole right face is
A ∪ W and all source ports lie outside it. Other boundary ports, if any,
play no role. All three observables are evaluated from their own traced endpoints. -/
theorem pure_retroreflection_counts (L : Finset P) (A W : Set P)
    (hL : (L : Set P) ⊆ g.boundary \ (A ∪ W)) (hAW : Disjoint A W) :
    (g.retro W).crossings L A = g.full.crossings L A ∧
    (g.retro W).fixedReturns L = g.full.crossings L W ∧
    g.full.crossings L (A ∪ W) = (g.retro W).crossings L A + (g.retro W).fixedReturns L := by
  have live {x : P} (hx : x ∈ L) : x ∈ (g.retro W).ports :=
    ⟨(hL hx).1, fun hw => (hL hx).2 (Or.inr hw)⟩
  have hcross : (g.retro W).crossings L A = g.full.crossings L A := by
    apply tally_congr
    intro x hx
    by_cases hw : g.full.endpoint x ∈ W
    · rw [g.retro_hits_wall (live hx) hw]
      exact iff_of_false (fun ha => (hL hx).2 (Or.inl ha))
        (fun ha => Set.disjoint_left.mp hAW ha hw)
    · rw [g.retro_misses_wall (live hx) hw]
  have hfixed : (g.retro W).fixedReturns L = g.full.crossings L W := by
    exact tally_congr (fun _ hx => g.retro_fixed_iff (live hx))
  refine ⟨hcross, hfixed, ?_⟩
  rw [hcross, hfixed]
  exact tally_or L _ _ (fun _ _ ha hw => Set.disjoint_left.mp hAW ha hw)

end Network
end MirrorPorts

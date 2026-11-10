import MirrorPorts.Counts
import Mathlib.Algebra.Group.Fin.Basic
import Mathlib.Data.Fintype.Prod
import Mathlib.Tactic.DeriveFintype

/-! The six-direction cubic lattice used by the sampler. Sizes are written as
successors so each axis has at least one site. The y and z axes are periodic. -/

namespace MirrorPorts.Slab

inductive Direction | xPlus | xMinus | yPlus | yMinus | zPlus | zMinus
  deriving DecidableEq, Fintype

structure Matching where
  partner : Direction → Direction
  involutive : Function.Involutive partner
  distinct : ∀ d, partner d ≠ d

abbrev Site (nx ny nz : ℕ) := Fin (nx + 1) × Fin (ny + 1) × Fin (nz + 1)
abbrev Port (nx ny nz : ℕ) := Site nx ny nz × Direction

variable {nx ny nz : ℕ}

/-- An exterior x-port is fixed. Each interior wire maps to the opposite
incident direction at the neighbour, including across a periodic seam. -/
def wire : Port nx ny nz → Port nx ny nz
  | ((x, y, z), .xPlus) =>
    if h : x.val < nx then ((⟨x.val + 1, by omega⟩, y, z), .xMinus)
    else ((x, y, z), .xPlus)
  | ((x, y, z), .xMinus) =>
    if h : 0 < x.val then ((⟨x.val - 1, by omega⟩, y, z), .xPlus)
    else ((x, y, z), .xMinus)
  | ((x, y, z), .yPlus) => ((x, y + 1, z), .yMinus)
  | ((x, y, z), .yMinus) => ((x, y - 1, z), .yPlus)
  | ((x, y, z), .zPlus) => ((x, y, z + 1), .zMinus)
  | ((x, y, z), .zMinus) => ((x, y, z - 1), .zPlus)

theorem wire_involutive : Function.Involutive (wire (nx := nx) (ny := ny) (nz := nz)) := by
  rintro ⟨⟨⟨x, hx⟩, y, z⟩, d⟩
  cases d with
  | xPlus =>
    by_cases h : x < nx <;> simp [wire, h]
  | xMinus =>
    by_cases h : 0 < x
    · have h' : x - 1 < nx := by omega
      simp [wire, h, h', Nat.sub_add_cancel h]
    · simp [wire, h]
  | yPlus | yMinus | zPlus | zMinus => simp [wire]

/-- Each vertex chooses its own matching. No endpoint or strand appears as input. -/
def network (env : Site nx ny nz → Matching) : Network (Port nx ny nz) where
  mirror p := (p.1, (env p.1).partner p.2)
  mirror_inv := fun ⟨v, d⟩ => congrArg (v, ·) ((env v).involutive d)
  mirror_ne := fun ⟨v, d⟩ h => (env v).distinct d (congrArg Prod.snd h)
  wire := wire
  wire_inv := wire_involutive

def leftFace : Set (Port nx ny nz) := {p | p.1.1.val = 0 ∧ p.2 = .xMinus}

def rightFace : Set (Port nx ny nz) := {p | p.1.1.val = nx ∧ p.2 = .xPlus}

theorem boundary_eq_faces (env : Site nx ny nz → Matching) :
    (network env).boundary = leftFace ∪ rightFace := by
  ext p
  rcases p with ⟨⟨⟨x, hx⟩, y, z⟩, d⟩
  cases d with
  | xPlus =>
    by_cases hr : x < nx <;> simp [Network.boundary, network, wire, leftFace, rightFace, hr] <;> omega
  | xMinus =>
    by_cases hl : 0 < x <;> simp_all [Network.boundary, network, wire, leftFace, rightFace]
  | yPlus | yMinus | zPlus | zMinus =>
    simp [Network.boundary, network, wire, leftFace, rightFace]

def leftPorts (nx ny nz : ℕ) : Finset (Port nx ny nz) :=
  Finset.univ.filter (fun p => p.1.1.val = 0 ∧ p.2 = .xMinus)

def counted (mask : Fin (ny + 1) → Fin (nz + 1) → Bool) : Set (Port nx ny nz) :=
  {p ∈ rightFace | mask p.1.2.1 p.1.2.2 = true}

def wall (mask : Fin (ny + 1) → Fin (nz + 1) → Bool) : Set (Port nx ny nz) :=
  {p ∈ rightFace | mask p.1.2.1 p.1.2.2 = false}

theorem right_split (mask : Fin (ny + 1) → Fin (nz + 1) → Bool) :
    counted (nx := nx) mask ∪ wall mask = rightFace := by
  ext p
  cases hm : mask p.1.2.1 p.1.2.2 <;> simp [counted, wall, hm]

/-- Pathwise reduction for every fixed cubic-lattice environment and every mask. -/
theorem cubic_reduction (env : Site nx ny nz → Matching)
    (mask : Fin (ny + 1) → Fin (nz + 1) → Bool) :
    let g := network env
    let L := leftPorts nx ny nz
    let A := counted (nx := nx) mask
    let W := wall (nx := nx) mask
    (g.retro W).crossings L A = g.full.crossings L A ∧
    (g.retro W).fixedReturns L = g.full.crossings L W ∧
    g.full.crossings L rightFace = (g.retro W).crossings L A + (g.retro W).fixedReturns L := by
  have hL : (leftPorts nx ny nz : Set (Port nx ny nz)) ⊆
      (network env).boundary \ (counted mask ∪ wall mask) := by
    intro p hp
    have hl : p ∈ leftFace := (Finset.mem_filter.mp hp).2
    rw [boundary_eq_faces, right_split]
    exact ⟨Or.inl hl, fun hr => Direction.noConfusion (hl.2.symm.trans hr.2)⟩
  have hAW : Disjoint (counted (nx := nx) mask) (wall mask) :=
    Set.disjoint_left.mpr (fun _ ha hw => Bool.noConfusion (ha.2.symm.trans hw.2))
  simpa only [right_split] using
    (network env).pure_retroreflection_counts (leftPorts nx ny nz) (counted mask) (wall mask) hL hAW

end MirrorPorts.Slab

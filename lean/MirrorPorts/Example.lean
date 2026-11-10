import MirrorPorts.Slab

/-! A two-lane example with an interior link and one retroreflecting outlet. -/

namespace MirrorPorts.Slab.Example

open Direction

private def opposite : Direction → Direction
  | xPlus => xMinus | xMinus => xPlus
  | yPlus => yMinus | yMinus => yPlus
  | zPlus => zMinus | zMinus => zPlus

private def straight : Matching :=
  ⟨opposite, fun d => by cases d <;> rfl, fun d => by cases d <;> decide⟩

/-- A two-layer slab with two straight lanes. -/
abbrev twoLaneModel := network (fun _ : Site 1 1 0 => straight)

def port (x y : Fin 2) (d : Direction) : Port 1 1 0 := ((x, y, 0), d)

/-- The right outlet in lane zero is open. -/
def mask (y : Fin 2) (_ : Fin 1) : Bool := decide (y = 0)

private theorem full_path (y : Fin 2) : twoLaneModel.Trace twoLaneModel.boundary (port 0 y xMinus)
    [port 0 y xMinus, port 1 y xMinus] (port 1 y xPlus) := by
  apply Network.Trace.more
  · intro h
    have hd : xMinus = xPlus := congrArg Prod.snd h
    cases hd
  · exact Network.Trace.one (port 1 y xMinus)

/-- The mirror encounters themselves are displayed, including the two reversed
encounters in lane 1. The mask passes lane 0 and reflects lane 1. -/
theorem two_lane_paths :
    let d := twoLaneModel.retro (wall mask)
    twoLaneModel.Trace d.ports (port 0 0 xMinus) [port 0 0 xMinus, port 1 0 xMinus] (port 1 0 xPlus) ∧
    twoLaneModel.Trace d.ports (port 0 1 xMinus)
      [port 0 1 xMinus, port 1 1 xMinus, port 1 1 xPlus, port 0 1 xPlus] (port 0 1 xMinus) := by
  constructor
  · exact (full_path 0).weaken (twoLaneModel.retro (wall mask)).exterior
  · exact twoLaneModel.retraced_path (wall mask) (full_path 1) rfl ⟨⟨rfl, rfl⟩, rfl⟩

private theorem full_end (y : Fin 2) : twoLaneModel.full.endpoint (port 0 y xMinus) = port 1 y xPlus :=
  twoLaneModel.full.endpoint_eq_of_trace rfl (full_path y) rfl

/-- In this slab N = 2, C_retro = 1 and f_L = 1. -/
theorem two_lane_counts :
    let L := leftPorts 1 1 0
    let d := twoLaneModel.retro (wall mask)
    twoLaneModel.full.crossings L rightFace = 2 ∧ d.crossings L (counted mask) = 1 ∧ d.fixedReturns L = 1 := by
  classical
  have hleft : leftPorts 1 1 0 = {port 0 0 xMinus, port 0 1 xMinus} := by decide
  have one_hit (target : Set (Port 1 1 0)) (y : Fin 2)
      (h : ∀ k, port 1 k xPlus ∈ target ↔ k = y) :
      twoLaneModel.full.crossings (leftPorts 1 1 0) target = 1 := by
    rw [Network.Detectors.crossings_eq_card]
    have hs : (leftPorts 1 1 0).filter (fun x => twoLaneModel.full.endpoint x ∈ target) =
        {port 0 y xMinus} := by
      ext x
      simp only [Finset.mem_filter, Finset.mem_singleton]
      constructor
      · rintro ⟨hx, ht⟩
        rw [hleft] at hx
        simp only [Finset.mem_insert, Finset.mem_singleton] at hx
        rcases hx with rfl | rfl <;> rw [full_end, h] at ht <;> subst y <;> rfl
      · rintro rfl
        exact ⟨Finset.mem_filter.mpr ⟨Finset.mem_univ _, rfl, rfl⟩, (full_end y) ▸ (h y).2 rfl⟩
    rw [hs, Finset.card_singleton]
  have hA : twoLaneModel.full.crossings (leftPorts 1 1 0) (counted mask) = 1 := by
    apply one_hit _ 0
    intro k
    simp [counted, mask, port, rightFace]
  have hW : twoLaneModel.full.crossings (leftPorts 1 1 0) (wall mask) = 1 := by
    apply one_hit _ 1
    intro k
    simp [wall, mask, port, rightFace]
    omega
  obtain ⟨hC, hF, hN⟩ := cubic_reduction (fun _ : Site 1 1 0 => straight) mask
  change (twoLaneModel.retro (wall mask)).crossings (leftPorts 1 1 0) (counted mask) = _ at hC
  change (twoLaneModel.retro (wall mask)).fixedReturns (leftPorts 1 1 0) = _ at hF
  exact ⟨by simpa only [hC, hF, hA, hW] using hN, hC.trans hA, hF.trans hW⟩

end MirrorPorts.Slab.Example

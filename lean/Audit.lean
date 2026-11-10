import MirrorPorts
import Lean.Util.CollectAxioms

open Lean Elab Command

-- Audit all declarations from these modules, including private helpers.
run_cmd
  let env ← getEnv
  let allowed := #[``propext, ``Classical.choice, ``Quot.sound]
  let mut count := 0
  for mod in env.header.modules do
    if `MirrorPorts |>.isPrefixOf mod.module then
      let some idx := env.getModuleIdx? mod.module | throwError "Missing module {mod.module}"
      let decls := env.header.moduleData[idx]!.constants
      for decl in decls do
        if decl matches .axiomInfo _ then
          throwError "Project axiom {decl.name}"
        let axioms ← Lean.collectAxioms decl.name
        let extra := axioms.filter (fun a => !allowed.contains a)
        unless extra.isEmpty do throwError "{decl.name} uses {extra}"
      count := count + decls.size
      logInfo m!"{mod.module}: checked {decls.size} declarations"
  if count == 0 then throwError "No project declarations audited"
  logInfo m!"Checked {count} project declarations"

#check @MirrorPorts.Network.open_path_or_cycle
#check @MirrorPorts.Network.retraced_path
#check @MirrorPorts.Network.Detectors.terminal_port_identity
#check @MirrorPorts.Slab.cubic_reduction
#check MirrorPorts.Slab.Example.two_lane_counts

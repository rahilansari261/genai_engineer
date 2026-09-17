/**
 * ============================================================================
 *  ATTACK LIST — the "red team" sidebar
 * ============================================================================
 * A simple list of buttons, one per canned attack from backend/guardrails.py.
 * Clicking one doesn't send anything itself — it just hands the attack up
 * to the parent page (via `onSelect`), which fills the message box with it.
 * This keeps the component "dumb": it doesn't know or care HOW its
 * selection gets used, it just reports "the user picked this one".
 * ============================================================================
 */

import type { Attack } from "@/lib/types";

export default function AttackList({
  attacks,
  onSelect,
  disabled,
}: {
  attacks: Attack[];
  onSelect: (attack: Attack) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm font-medium opacity-70">Red team attacks</h2>
      <p className="text-xs opacity-50">
        Click one to load it into the message box, then hit Send.
      </p>

      <div className="flex flex-col gap-2">
        {attacks.map((attack) => (
          <button
            key={attack.id}
            disabled={disabled}
            onClick={() => onSelect(attack)}
            className="rounded-lg border border-black/10 dark:border-white/15 px-3 py-2 text-left text-xs hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-40"
          >
            <div className="font-medium">{attack.label}</div>
            <div className="opacity-50">{attack.category}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

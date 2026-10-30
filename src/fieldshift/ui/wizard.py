"""ui/wizard.py — interview state machine (Phase 3)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .prompter import BACK, Prompter
from .questions import CATALOG, Question, next_question_id, question_by_id, resolve_choices
from .screens import banner, flags_list, step_header, summary_table


class Wizard:
    def __init__(self, prompter: Prompter, crop_ids: list[str],
                 template_ids: list[str], data_dir: Path, ui, console):
        self.prompter = prompter
        self.crop_ids = crop_ids
        self.template_ids = template_ids
        self.data_dir = Path(data_dir)
        self.ui = ui
        self.console = console
        self.answers: dict[str, Any] = {}
        self.asked: set[str] = set()
        self.history: list[str] = []  # answered question ids in order
        self.flags: list[str] = []
        self.chosen_priorities: list[str] = []

    def ctx(self) -> dict:
        return {"crop_ids": self.crop_ids, "template_ids": self.template_ids,
                "chosen_priorities": self.chosen_priorities}

    def _save_draft(self) -> None:
        draft = self.data_dir / "runs" / "draft.json"
        draft.parent.mkdir(parents=True, exist_ok=True)
        payload = {"answers": self.answers, "history": self.history, "flags": self.flags,
                   "saved_at": datetime.now().isoformat(timespec="seconds")}
        draft.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_draft(self) -> bool:
        draft = self.data_dir / "runs" / "draft.json"
        if not draft.is_file():
            return False
        try:
            payload = json.loads(draft.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        self.answers = payload.get("answers", {})
        self.history = payload.get("history", [])
        self.asked = set(self.history)
        self.flags = payload.get("flags", [])
        self.chosen_priorities = self.answers.get("prio_rank_list", [])
        return True

    def _record_unknown_flag(self, q: Question) -> None:
        if q.unknown_flag and q.unknown_flag not in self.flags:
            self.flags.append(q.unknown_flag)

    def _handle_answer(self, q: Question, ans: Any) -> None:
        self.answers[q.id] = ans
        self.asked.add(q.id)
        self.history.append(q.id)
        # priority ranking accumulation
        if q.id == "prio_rank":
            if ans == "__stop__":
                self.chosen_priorities = self.chosen_priorities  # no change
            else:
                if ans not in self.chosen_priorities:
                    self.chosen_priorities.append(ans)
        if ans == "__unknown__":
            self._record_unknown_flag(q)
        if ans is None and q.unknown_flag:
            # skippable -> unknown handling for soil fields
            self._record_unknown_flag(q)
        self._save_draft()

    def run(self) -> dict:
        banner(self.console, self.ui, version="0.1.0")
        # resume prompt
        # determine total steps (approximate)
        total = len(CATALOG)
        step = 1
        while True:
            qid = next_question_id(self.answers, self.asked)
            if qid is None:
                break
            q = question_by_id(qid)
            if q is None:
                break
            # skip questions whose condition is false (already handled by next_question_id)
            choices = q.choices
            if isinstance(choices, str):
                choices = resolve_choices(q, self.ctx())
            step_header(self.console, self.ui, q.header, step, total)
            if q.help_text:
                self.console.print(f"[muted]{q.help_text}[/muted]")

            # ask
            try:
                if q.kind == "select":
                    ans = self.prompter.select(q.id, q.header, q.prompt, choices,
                                               help_text=q.help_text, allow_back=True)
                elif q.kind == "multi":
                    ans = self.prompter.multi_select(q.id, q.header, q.prompt, choices,
                                                    min_select=q.min_select, help_text=q.help_text)
                elif q.kind == "text":
                    ans = self.prompter.text(q.id, q.header, q.prompt, help_text=q.help_text,
                                             skippable=q.skippable)
                elif q.kind == "number":
                    ans = self.prompter.number(q.id, q.header, q.prompt, help_text=q.help_text,
                                               skippable=q.skippable, min_val=q.min_val,
                                               max_val=q.max_val)
                elif q.kind == "confirm":
                    default = getattr(q, "default", False)
                    ans = self.prompter.confirm(
                        q.id, q.header, q.prompt, help_text=q.help_text, default=default
                    )
                else:
                    ans = None
            except KeyboardInterrupt:
                self._ctrl_c_menu()
                continue

            if ans is BACK:
                # go back: remove last answered
                if self.history:
                    last = self.history.pop()
                    self.asked.discard(last)
                    self.answers.pop(last, None)
                    if last == "prio_rank" and self.chosen_priorities:
                        self.chosen_priorities.pop()
                continue

            # prio_rank special: loop until __stop__ or all chosen
            if q.id == "prio_rank" and ans != "__stop__":
                self._handle_answer(q, ans)
                # if more priorities remain, re-ask prio_rank
                remaining = [p for p in ["reduce_water_use", "support_soil_health",
                                         "improve_climate_resilience", "maintain_productivity"]
                             if p not in self.chosen_priorities]
                if remaining and len(self.chosen_priorities) < 4:
                    # re-ask prio_rank: remove from asked so next_question_id re-offers
                    self.asked.discard("prio_rank")
                    self.history.pop()
                    step += 1
                    continue
                # store the ordered list
                self.answers["prio_rank_list"] = list(self.chosen_priorities)
                step += 1
                continue

            # coords_real default attribute
            self._handle_answer(q, ans)
            step += 1

        # summary
        self._finalize_soil()
        self._summary()
        return self.answers

    def _ctrl_c_menu(self) -> None:
        self.console.print("\n[warn]Interrupted.[/warn]")
        self.console.print("  1. Resume")
        self.console.print("  2. Save draft & quit")
        self.console.print("  3. Quit without saving")
        try:
            raw = input("> ").strip()
        except EOFError:
            raw = "3"
        if raw == "2":
            self._save_draft()
            raise SystemExit(0)
        if raw == "3":
            raise SystemExit(130)
        # 1 = resume: do nothing

    def _finalize_soil(self) -> None:
        from ..data.soil import load_soil, merge_farmer_test, soil_path
        # compute locid
        if self.answers.get("loc_mode") == "pilot":
            lat, lon = 31.04, 31.38
        else:
            lat = self.answers.get("lat")
            lon = self.answers.get("lon")
            if lat is None or lon is None:
                return
        locid = f"{float(lat):.2f}_{float(lon):.2f}"
        path = soil_path(self.data_dir, locid)
        record = load_soil(path) if path.is_file() else {}
        if not record:
            record = {"schema_version": 1, "location_id": locid, "fields": {}}
        if self.answers.get("soil_test") is True:
            ft = {"fields": {}}
            tex = self.answers.get("soil_texture")
            if tex and tex != "unknown":
                ft["fields"]["soil_texture"] = {"v": tex, "unit": "USDA class"}
            ph = self.answers.get("soil_ph")
            if ph is not None:
                ft["fields"]["soil_ph"] = {"v": ph, "unit": "pH"}
            oc = self.answers.get("soil_oc")
            if oc is not None:
                ft["fields"]["organic_carbon"] = {"v": oc, "unit": "%"}
            ec = self.answers.get("soil_ec")
            if ec is not None:
                ft["fields"]["soil_ec_dsm"] = {"v": ec, "unit": "dS/m"}
            depth = self.answers.get("soil_depth")
            if depth is not None:
                ft["fields"]["soil_depth_cm"] = {"v": depth, "unit": "cm"}
            merged = merge_farmer_test(record, ft)
            path.parent.mkdir(parents=True, exist_ok=True)
            import json
            path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
        # store locid for later
        self.answers["_locid"] = locid

    def _summary(self) -> None:
        rows = []
        rows.append(("Location", str(self.answers.get("loc_mode")), "—"))
        rows.append(("Previous crop", str(self.answers.get("prev_crop")), "—"))
        rows.append(("Priorities", ", ".join(self.chosen_priorities) or "(equal)", "—"))
        rows.append(("Horizon (years)", str(self.answers.get("horizon")), "—"))
        rows.append(("Data mode", str(self.answers.get("data_mode")), "—"))
        summary_table(self.console, self.ui, rows)
        if self.flags:
            flags_list(self.console, self.ui, self.flags)
        self.console.print(
            "[muted]Check these locally with an agronomist or extension officer.[/muted]"
        )


def non_tty_exit() -> int:
    """Return exit code 2 with a helpful message when not a TTY."""
    import sys
    if not sys.stdin.isatty():
        print("fieldshift: this command needs an interactive terminal (TTY).")
        print("Use `fieldshift demo` for an offline scripted run, or pass --answers FILE.")
        return 2
    return 0

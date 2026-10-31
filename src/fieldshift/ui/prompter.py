"""ui/prompter.py — Prompter protocol + 3 implementations (Phase 3)."""

from __future__ import annotations

from typing import Any, Protocol

import questionary

BACK = object()  # sentinel returned when the user picks "← Back"


class Prompter(Protocol):
    def select(self, qid, header, question, choices, *, help_text=None, allow_back=True) -> Any: ...
    def multi_select(
        self, qid, header, question, choices, *, min_select=0, help_text=None
    ) -> Any: ...
    def text(
        self, qid, header, question, *, help_text=None, skippable=False, validate=None
    ) -> Any: ...
    def number(
        self,
        qid,
        header,
        question,
        *,
        help_text=None,
        skippable=False,
        min_val=None,
        max_val=None,
    ) -> Any: ...
    def confirm(self, qid, header, question, *, help_text=None, default=False) -> Any: ...


def _header_chip(header: str) -> str:
    return f"[ {header} ]"


class QuestionaryPrompter:
    """Interactive arrow-key prompter (default on a TTY)."""

    def __init__(self, ui):
        self.ui = ui

    def _choices_with_back(self, choices, allow_back):
        out = list(choices)
        if allow_back:
            out = [*out, ("← Back", BACK)]
        return out

    def select(self, qid, header, question, choices, *, help_text=None, allow_back=True):
        # choices: list of (label, value) or list of strings
        norm = [(c if isinstance(c, tuple) else (c, c)) for c in choices]
        if allow_back:
            norm = [*norm, ("← Back", BACK)]
        title = question
        q = questionary.select(
            title,
            choices=[questionary.Choice(title=label, value=val) for label, val in norm],
            style=self.ui.questionary_style(),
            instruction=(help_text or ""),
        )
        try:
            ans = q.ask()
        except KeyboardInterrupt:
            return BACK
        if ans is BACK:
            return BACK
        return ans

    def multi_select(self, qid, header, question, choices, *, min_select=0, help_text=None):
        norm = [(c if isinstance(c, tuple) else (c, c)) for c in choices]
        instruction = help_text or ""
        if min_select:
            selection_hint = (
                f"Select at least {min_select}: use Space to toggle choices, "
                "then press Enter to finish."
            )
            instruction = f"{instruction}\n{selection_hint}" if instruction else selection_hint
        while True:
            q = questionary.checkbox(
                question,
                choices=[questionary.Choice(title=label, value=val) for label, val in norm],
                style=self.ui.questionary_style(),
                instruction=instruction,
            )
            try:
                ans = q.ask()
            except KeyboardInterrupt:
                return BACK
            if ans is None:
                return BACK
            if len(ans) >= min_select:
                return ans
            print(
                f"You selected {len(ans)}. Select at least {min_select} alternatives "
                "with Space, then press Enter to finish."
            )

    def text(self, qid, header, question, *, help_text=None, skippable=False, validate=None):
        q = questionary.text(
            question, style=self.ui.questionary_style(), instruction=(help_text or "")
        )
        try:
            ans = q.ask()
        except KeyboardInterrupt:
            return BACK
        if ans is None:
            return BACK
        ans = ans.strip()
        if skippable and ans == "":
            return None
        if validate:
            err = validate(ans)
            if err:
                # re-ask once
                return self.text(
                    qid,
                    header,
                    question,
                    help_text=help_text,
                    skippable=skippable,
                    validate=validate,
                )
        return ans

    def number(
        self, qid, header, question, *, help_text=None, skippable=False, min_val=None, max_val=None
    ):
        def _parse(s):
            s = s.strip().replace(",", ".")
            # Arabic-Indic digits
            for a, b in zip("٠١٢٣٤٥٦٧٨٩", "0123456789", strict=True):
                s = s.replace(a, b)
            s = s.replace("٫", ".")
            if s == "":
                return None if skippable else _parse  # signal empty
            try:
                return float(s)
            except ValueError:
                return "ERR"

        while True:
            q = questionary.text(
                question, style=self.ui.questionary_style(), instruction=(help_text or "")
            )
            try:
                raw = q.ask()
            except KeyboardInterrupt:
                return BACK
            if raw is None:
                return BACK
            val = _parse(raw)
            if val is None and skippable:
                return None
            if val == "ERR":
                continue
            if min_val is not None and val < min_val:
                continue
            if max_val is not None and val > max_val:
                continue
            return val

    def confirm(self, qid, header, question, *, help_text=None, default=False):
        q = questionary.confirm(question, default=default, style=self.ui.questionary_style())
        try:
            ans = q.ask()
        except KeyboardInterrupt:
            return BACK
        if ans is None:
            return BACK
        return bool(ans)


class PlainPrompter:
    """Numbered menus + input() for --plain / non-colored / limited terminals."""

    def __init__(self, ui):
        self.ui = ui

    def _print(self, header, question, help_text):
        print(f"\n[ {header} ]")
        print(question)
        if help_text:
            print(f"  ({help_text})")

    def select(self, qid, header, question, choices, *, help_text=None, allow_back=True):
        norm = [(c if isinstance(c, tuple) else (c, c)) for c in choices]
        if allow_back:
            norm = [*norm, ("Back", BACK)]
        self._print(header, question, help_text)
        for i, (label, _) in enumerate(norm, 1):
            print(f"  {i}. {label}")
        while True:
            raw = input("> ").strip()
            try:
                idx = int(raw)
            except ValueError:
                continue
            if 1 <= idx <= len(norm):
                val = norm[idx - 1][1]
                return val
            # allow typing the label
            for label, val in norm:
                if label.lower() == raw.lower():
                    return val

    def multi_select(self, qid, header, question, choices, *, min_select=0, help_text=None):
        norm = [(c if isinstance(c, tuple) else (c, c)) for c in choices]
        self._print(header, question, help_text)
        for i, (label, _) in enumerate(norm, 1):
            print(f"  {i}. {label}")
        print("Enter comma-separated numbers (e.g. 1,3).")
        while True:
            raw = input("> ").strip()
            if raw == "":
                return []
            idxs = []
            ok = True
            for part in raw.split(","):
                part = part.strip()
                try:
                    i = int(part)
                except ValueError:
                    ok = False
                    break
                if not (1 <= i <= len(norm)):
                    ok = False
                    break
                idxs.append(i - 1)
            if ok and len(idxs) >= min_select:
                return [norm[i][1] for i in idxs]

    def text(self, qid, header, question, *, help_text=None, skippable=False, validate=None):
        self._print(header, question, help_text)
        while True:
            raw = input("> ").strip()
            if skippable and raw == "":
                return None
            if validate:
                err = validate(raw)
                if err:
                    print(f"  {err}")
                    continue
            return raw

    def number(
        self, qid, header, question, *, help_text=None, skippable=False, min_val=None, max_val=None
    ):
        self._print(header, question, help_text)
        while True:
            raw = input("> ").strip()
            if skippable and raw == "":
                return None
            s = raw.replace(",", ".")
            for a, b in zip("٠١٢٣٤٥٦٧٨٩", "0123456789", strict=True):
                s = s.replace(a, b)
            s = s.replace("٫", ".")
            try:
                val = float(s)
            except ValueError:
                print("  Please enter a number.")
                continue
            if min_val is not None and val < min_val:
                print(f"  Must be >= {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"  Must be <= {max_val}.")
                continue
            return val

    def confirm(self, qid, header, question, *, help_text=None, default=False):
        self._print(header, question, help_text)
        hint = "Y/n" if default else "y/N"
        raw = input(f"  ({hint}) > ").strip().lower()
        if raw == "":
            return default
        return raw in ("y", "yes", "1", "true")


class ScriptedPrompter:
    """Replays answers by Question.id (tests, demo, --answers file)."""

    def __init__(self, answers: dict):
        self.answers = dict(answers)
        self._seen: list[str] = []

    def _get(self, qid):
        if qid not in self.answers:
            raise KeyError(f"ScriptedPrompter: no answer for question id {qid!r}")
        val = self.answers[qid]
        if isinstance(val, list):
            if not val:
                raise KeyError(f"ScriptedPrompter: exhausted list for {qid!r}")
            val = val.pop(0)
            # store remainder back? already popped in place
        self._seen.append(qid)
        if val == "__BACK__":
            return BACK
        return val

    def select(self, qid, header, question, choices, *, help_text=None, allow_back=True):
        return self._get(qid)

    def multi_select(self, qid, header, question, choices, *, min_select=0, help_text=None):
        if qid not in self.answers:
            raise KeyError(f"ScriptedPrompter: no answer for question id {qid!r}")
        self._seen.append(qid)
        answer = self.answers[qid]
        if answer == "__BACK__":
            return BACK
        if not isinstance(answer, list):
            answer = [answer]
        if len(answer) < min_select:
            raise ValueError(f"select at least {min_select}")
        return answer

    def text(self, qid, header, question, *, help_text=None, skippable=False, validate=None):
        return self._get(qid)

    def number(
        self, qid, header, question, *, help_text=None, skippable=False, min_val=None, max_val=None
    ):
        return self._get(qid)

    def confirm(self, qid, header, question, *, help_text=None, default=False):
        return self._get(qid)

    @property
    def seen(self) -> list[str]:
        return list(self._seen)

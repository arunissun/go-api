"""
Deterministic draft assembly — Python port of src/utils/builder.ts (buildDeterministicDraft).

Accepts deserialized statement dicts and document context, returns a DeterministicDraft dict.
No Gemini calls here.
"""

import re

CONNECTOR_SENTINELS = {"custom-logic", "custom-transition"}


def _format_token_label(value: str) -> str:
    parts = re.split(r"[-_\s]+", value)
    return " ".join(part.capitalize() for part in parts if part)


def _describe_operator(op: str) -> str:
    mapping = {
        ">=": "reaches or exceeds",
        ">": "exceeds",
        "<=": "falls to or below",
        "<": "falls below",
        "==": "equals",
        "reduction": "shows a reduction to",
    }
    return mapping.get(op, op)


def _assemble_clause(s: dict) -> str:
    if s.get("isFreeText"):
        return (s.get("freeTextStatement") or "").strip() or "[free-text statement]"

    var = s.get("canonicalVariable") or ""
    var_part = "[custom variable]" if not var or var == "custom" else var

    subcat = s.get("subcategory") or ""
    if subcat == "custom":
        subcat_part = "([custom subcategory])"
    elif subcat:
        subcat_part = f"({subcat})"
    else:
        subcat_part = ""

    op_part = _describe_operator(s.get("operator") or ">=")
    value_part = s.get("thresholdValue") or "[threshold]"

    unit = s.get("thresholdUnit") or ""
    unit_part = "[unit]" if not unit or unit == "custom" else unit

    threshold_clause = " ".join(filter(None, [var_part, subcat_part, op_part, value_part, unit_part]))

    geo_type = s.get("geographyType") or "national"
    geo_label = s.get("geographyLabel") or ""
    if geo_type == "national":
        geo_part = "at national scope"
    else:
        label_suffix = f" ({geo_label})" if geo_label else ""
        geo_part = f"for {_format_token_label(geo_type)}{label_suffix}"

    lead_time = s.get("leadTimeValue")
    timeframe = s.get("timeframeUnit") or "days"
    lead_time_part = f"within {lead_time} {timeframe}" if lead_time else ""

    prob = s.get("probabilityValue")
    prob_part = f"with {prob}% probability" if prob is not None else ""

    source = s.get("sourceAuthority") or ""
    source_part = f"as monitored by {source}" if source else ""

    notes = (s.get("notes") or "").strip()
    notes_part = f"[note: {notes}]" if notes else ""

    return ", ".join(filter(None, [threshold_clause, geo_part, lead_time_part, prob_part, source_part, notes_part]))


def _join_phase_statements(phase_stmts: list[dict]) -> str:
    parts: list[str] = []
    for idx, s in enumerate(phase_stmts):
        clause = _assemble_clause(s)
        if idx < len(phase_stmts) - 1:
            within = s.get("withinConnector") or ""
            cross = s.get("crossConnector") or ""
            if within and within not in CONNECTOR_SENTINELS:
                raw = within
            elif cross and cross not in CONNECTOR_SENTINELS:
                raw = cross
            else:
                raw = "AND"
            display = f"[{raw}]" if raw == raw.upper() else raw
            parts.append(f"{clause} {display}")
        else:
            parts.append(clause)
    return " ".join(parts)


def build_deterministic_draft(metadata: dict, statements: list[dict]) -> dict:
    """
    Returns:
        {preActivation, activation, stop, combined}
    """
    phase_order = ["pre_activation", "activation", "stop"]

    def phase_index(s: dict) -> int:
        p = s.get("phase", "activation")
        return phase_order.index(p) if p in phase_order else 99

    sorted_stmts = sorted(statements, key=phase_index)

    pre_stmts = [s for s in sorted_stmts if s.get("phase") == "pre_activation"]
    act_stmts = [s for s in sorted_stmts if s.get("phase") == "activation"]
    stop_stmts = [s for s in sorted_stmts if s.get("phase") == "stop"]

    pre_activation = _join_phase_statements(pre_stmts) if pre_stmts else ""
    activation = _join_phase_statements(act_stmts) if act_stmts else ""
    stop = _join_phase_statements(stop_stmts) if stop_stmts else ""

    raw_pre_act = metadata.get("interPhasePreToAct") or "PRECEDES"
    raw_act_stop = metadata.get("interPhaseActToStop") or "ENABLES"
    inter_pre_to_act = raw_pre_act if raw_pre_act not in CONNECTOR_SENTINELS else "PRECEDES"
    inter_act_to_stop = raw_act_stop if raw_act_stop not in CONNECTOR_SENTINELS else "ENABLES"

    combined_parts: list[str] = []
    if pre_activation:
        combined_parts.append(f"[Pre-activation] {pre_activation}")
    if pre_activation and activation:
        combined_parts.append(f"[{inter_pre_to_act}]")
    if activation:
        combined_parts.append(f"[Activation] {activation}")
    if activation and stop:
        combined_parts.append(f"[{inter_act_to_stop}]")
    if stop:
        combined_parts.append(f"[Stop mechanism] {stop}")

    combined = " ".join(combined_parts) if combined_parts else "[No trigger conditions entered]"

    return {
        "preActivation": pre_activation,
        "activation": activation,
        "stop": stop,
        "combined": combined,
    }

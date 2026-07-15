"""
Structural validation for trigger builder requests.
Returns (warnings, errors) tuples — no I/O, no Django imports.
"""


def validate_document_context(doc: dict) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    if not doc.get("countryId"):
        errors.append("documentContext: countryId is required.")
    if not (doc.get("countryIso3") or "").strip():
        errors.append("documentContext: countryIso3 is required.")
    if not (doc.get("countryName") or "").strip():
        errors.append("documentContext: countryName is required.")
    if not doc.get("hazardTypes"):
        warnings.append("documentContext: hazardTypes is empty.")
    return warnings, errors


def validate_statement(s: dict) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    sid = s.get("id", "?")
    phase = (s.get("phase") or "").strip()
    if not phase:
        errors.append(f"Statement {sid}: phase is required.")

    if s.get("isFreeText"):
        if not (s.get("freeTextStatement") or "").strip():
            errors.append(f"Statement {sid}: isFreeText is true but freeTextStatement is empty.")
    else:
        if not (s.get("canonicalVariable") or "").strip():
            warnings.append(f"Statement {sid}: canonicalVariable is empty.")
        if not (s.get("thresholdValue") or "").strip():
            errors.append(f"Statement {sid}: thresholdValue is required for structured statements.")
        geo_type = s.get("geographyType") or "national"
        label_required_for = {"station_gauge", "watershed_basin", "administrative_unit", "regional"}
        if geo_type in label_required_for and not (s.get("geographyLabel") or "").strip():
            warnings.append(
                f"Statement {sid}: geographyLabel is recommended for geographyType '{geo_type}'."
            )
        if geo_type in label_required_for and not s.get("geographyConfirmed"):
            errors.append(f"Statement {sid}: geography must be confirmed through Mapbox.")

    return warnings, errors

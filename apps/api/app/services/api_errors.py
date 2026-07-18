from sqlalchemy.exc import IntegrityError


def invoice_create_error_message(exc: Exception) -> tuple[int, str]:
    """Map invoice creation failures to safe client-facing messages."""
    message = str(exc).lower()

    if isinstance(exc, IntegrityError) or "integrityerror" in message:
        if "invoice_number" in message:
            return (
                409,
                "An invoice with this number already exists. Please try again.",
            )
        return 409, "Could not create invoice due to a conflict. Please try again."

    if "uniqueviolation" in message:
        if "invoice_number" in message:
            return (
                409,
                "An invoice with this number already exists. Please try again.",
            )
        return 409, "Could not create invoice due to a conflict. Please try again."

    return 500, "Failed to create invoice. Please try again."

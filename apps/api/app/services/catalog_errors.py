from sqlalchemy.exc import IntegrityError


def category_create_error_message(exc: Exception) -> tuple[int, str]:
    message = str(exc).lower()

    if isinstance(exc, IntegrityError) or "integrityerror" in message:
        if "product_categories_user_name" in message or (
            "unique" in message and "product_categories" in message
        ):
            return 409, "A category with this name already exists."
        if "product_categories_user_id_fkey" in message or (
            "foreign key" in message and "users" in message
        ):
            return 409, "Your account is not provisioned yet. Please try again."
        return 409, "Could not create category due to a conflict. Please try again."

    return 500, "Failed to create category. Please try again."


def product_create_error_message(exc: Exception) -> tuple[int, str]:
    message = str(exc).lower()

    if isinstance(exc, IntegrityError) or "integrityerror" in message:
        if "idx_products_user_sku" in message or (
            "unique" in message and "sku" in message
        ):
            return 409, "A product with this SKU already exists."
        if "products_user_id_fkey" in message or (
            "foreign key" in message and "users" in message
        ):
            return 409, "Your account is not provisioned yet. Please try again."
        return 409, "Could not create product due to a conflict. Please try again."

    return 500, "Failed to create product. Please try again."

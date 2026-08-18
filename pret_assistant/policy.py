from .models import KnowledgeDocument, UserContext


def is_document_allowed(user: UserContext, document: KnowledgeDocument) -> bool:
    if not user.user_id.strip():
        return False

    if document.market and document.market.casefold() != user.market.casefold():
        return False

    if document.allowed_groups and not user.groups.intersection(document.allowed_groups):
        return False

    if document.allowed_store_ids:
        if user.store_id is None or user.store_id not in document.allowed_store_ids:
            return False

    return True

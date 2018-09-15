class EqualsError(Exception):
    """
    Signals an error while accessing the configuration.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)


def equals(a, b, relaxed_order=False):
    """
    Equalness is determined by relevant members (see also https://stackoverflow.com/a/25176504)
    """

    if not isinstance(a, b.__class__):
        raise EqualsError('Equals of different classes not supported.')

    items_a = a.get_equality_relevant_items()
    items_b = b.get_equality_relevant_items()

    if relaxed_order:
        return set(items_a) == set(items_b)

    return items_a == items_b


def calculate_hash(a, relaxed_order=False):
    """
    The hash is computed from the equality-relevant-items only.
    """

    items = a.get_equality_relevant_items()

    if relaxed_order:
        return hash(frozenset(items))

    return hash(tuple(items))

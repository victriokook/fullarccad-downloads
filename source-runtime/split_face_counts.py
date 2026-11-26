def checked_face_counts(before,after,solids):
    if isinstance(before, bool) or isinstance(after, bool) or isinstance(solids, bool):
        raise ValueError("Split must add 1..200 faces while preserving one solid")
    if not isinstance(before, int) or not isinstance(after, int) or not isinstance(solids, int):
        raise ValueError("Split must add 1..200 faces while preserving one solid")
    if before < 1 or before > 200:
        raise ValueError("Split must add 1..200 faces while preserving one solid")
    if after <= before or after > 400:
        raise ValueError("Split must add 1..200 faces while preserving one solid")
    if after - before > 200:
        raise ValueError("Split must add 1..200 faces while preserving one solid")
    if solids != 1:
        raise ValueError("Split must add 1..200 faces while preserving one solid")
    return after - before

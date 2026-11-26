


ALIGNMENTS = (
    "Top-Left", "Top-Center", "Top-Right",
    "Middle-Left", "Middle-Center", "Middle-Right",
    "Bottom-Left", "Bottom-Center", "Bottom-Right"
)

REFERENCES = ("Cap Height", "Shape Height")


def checked_alignment(alignment, reference):
    if alignment is not None and (type(alignment) is not str or alignment not in ALIGNMENTS):
        raise ValueError("Invalid alignment")
    if reference is not None and (type(reference) is not str or reference not in REFERENCES):
        raise ValueError("Invalid reference")
    return alignment,reference

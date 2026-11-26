import pathlib


def validate_options(precision, filename):
    # Validate precision
    if type(precision) is not int:
        raise ValueError("precision must be an exact int")
    if precision < 3 or precision > 6:
        raise ValueError("precision must be between 3 and 6 inclusive")

    # Validate filename
    if type(filename) is not str:
        raise ValueError("filename must be a string")
    if len(filename) == 0:
        raise ValueError("filename must be nonempty")
    if len(filename) > 1024:
        raise ValueError("filename length must be <= 1024")
    if '\0' in filename:
        raise ValueError("filename must not contain NUL")
    if '\r' in filename:
        raise ValueError("filename must not contain CR")
    if '\n' in filename:
        raise ValueError("filename must not contain LF")

    # Validate suffix
    # Check case-insensitive suffix .nc or .ngc
    lower_filename = filename.lower()
    if not (lower_filename.endswith('.nc') or lower_filename.endswith('.ngc')):
        raise ValueError("filename must have suffix .nc or .ngc (case-insensitive)")

    return (precision, filename)

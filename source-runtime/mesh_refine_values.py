"""Conservative native refine capacity, not an exact facet prediction."""
import math


def _validate_int(value):
    """Validate that value is an exact int, not bool or subclass."""
    if type(value) is bool:
        raise ValueError("Input must be an exact int, not bool")
    if type(value) is not int:
        raise ValueError("Input must be an exact int")


def _validate_facets(facets):
    """Validate facets input."""
    _validate_int(facets)
    if facets < 1 or facets > 20000:
        raise ValueError("facets must be between 1 and 20000")


def _validate_iterations(iterations):
    """Validate iterations input."""
    _validate_int(iterations)
    if iterations < 1 or iterations > 3:
        raise ValueError("iterations must be between 1 and 3")


def checked(iterations, facets):
    """
    Check mesh refinement values.
    
    Args:
        iterations: Number of refinement iterations (1-3)
        facets: Number of initial facets (1-20000)
    
    Returns:
        Tuple of (iterations, conservative_upper_facets)
    
    Raises:
        ValueError: If inputs are invalid or conservative capacity exceed 20000
    """
    _validate_iterations(iterations)
    _validate_facets(facets)
    
    predicted = facets * (3 ** iterations)
    
    if predicted > 20000:
        raise ValueError(f"Conservative capacity {predicted} exceeds maximum 20000")
    
    return (iterations, predicted)


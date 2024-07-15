"""
The :mod:`idakit` module implements algorithms, including

#. Feature expansion
#. Feature selection
#. Narx model
#. Pipeline models
"""

from ._expansion import (
    PolyBasis,
    RadialBasis,
    make_poly_ids,
    make_rbf_ids,
)

__all__ = [
    "PolyBasis",
    "make_poly_ids",
    "RadialBasis",
    "make_rbf_ids",
]

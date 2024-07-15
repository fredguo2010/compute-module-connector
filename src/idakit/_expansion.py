"""
The module contains feature expansion tools.
"""

import math
from itertools import combinations_with_replacement
from numbers import Integral, Real

# from collections import deque
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils import check_array
from sklearn.utils._param_validation import Interval, validate_params
from sklearn.utils.validation import check_is_fitted, check_random_state


@validate_params(
    {
        "X": ["array-like"],
        "n_features": [
            Interval(Integral, 0, None, closed="left"),
        ],
        "random_state": ["random_state"],
    },
    prefer_skip_nested_validation=True,
)
def make_rbf_ids(
    X,
    n_features=0,
    random_state=None,
):
    """Generate ids for radial basis features.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        The data.

    n_features: int, default=0
        The number of input features.

    random_state :  int, RandomState instance or None (default)
        Determines random number generation for dataset random sampling. It is not
        used for dataset shuffling.
        Pass an int for reproducible output across multiple function calls.
        See :term:`Glossary <random_state>`.

    Returns
    -------
    ids : array-like of shape (`n_output_features_`, degree)
        The unique id numbers of output features.
    """
    X = check_array(array=X, ensure_2d=True, dtype=np.float64)
    rng = check_random_state(random_state)
    n_samples = X.shape[0]

    if n_features > n_samples:
        raise ValueError(
            f"n_features {n_features} must be less than n_samples {n_samples}."
        )

    rand_idx = rng.choice(n_samples, n_features, replace=False)
    ids = X[rand_idx, :]
    return ids


@validate_params(
    {
        "n_features": [
            Interval(Integral, 1, None, closed="left"),
        ],
        "max_delay": [
            Interval(Integral, 1, None, closed="left"),
        ],
        "include_zero_delay": ["boolean", "array-like"],
    },
    prefer_skip_nested_validation=True,
)
def make_time_shift_ids(
    n_features=1,
    max_delay=1,
    include_zero_delay=False,
):
    """Generate ids for time shift features.

    Parameters
    ----------
    n_features: int, default=1
        The number of input features.

    max_delay : int, default=1
        The maximum delay of time shift features.

    include_zero_delay : {bool, array-like} of shape (n_features,) default=False
        Whether to include the original (zero-delay) features.

    Returns
    -------
    ids : array-like of shape (`n_output_features_`, degree)
        The unique id numbers of output features.
    """
    if isinstance(include_zero_delay, bool):
        return np.stack(
            np.meshgrid(
                range(n_features),
                range(not include_zero_delay, max_delay + 1),
                indexing="ij",
            ),
            -1,
        ).reshape(-1, 2)

    include_zero_delay = check_array(include_zero_delay, ensure_2d=False, dtype=bool)
    if include_zero_delay.shape[0] != n_features:
        raise ValueError(
            f"The length of `include_zero_delay`={include_zero_delay} "
            f"should be equal to `n_features`={n_features}."
        )

    ids = np.stack(
        np.meshgrid(
            range(n_features),
            range(max_delay + 1),
            indexing="ij",
        ),
        -1,
    ).reshape(-1, 2)
    exclude_zero_delay_idx = np.where(~include_zero_delay)[0]
    mask = np.isin(ids[:, 0], exclude_zero_delay_idx) & (ids[:, 1] == 0)
    return ids[~mask]


@validate_params(
    {
        "n_features": [
            Interval(Integral, 1, None, closed="left"),
        ],
        "degree": [
            None,
            Interval(Integral, 1, None, closed="left"),
        ],
    },
    prefer_skip_nested_validation=True,
)
def make_poly_ids(
    n_features=1,
    degree=1,
):
    """Generate ids for polynomial features.

    Parameters
    ----------
    n_features: int, default=1
        The number of input features.

    degree : int, default=1
        The maximum degree of polynomial features.

    Returns
    -------
    ids : array-like of shape (`n_output_features_`, degree)
        The unique id numbers of output features.
    """
    n_out = math.comb(n_features + degree, degree) - 1
    if n_out > np.iinfo(np.intp).max:
        msg = (
            "The output that would result from the current configuration would"
            f" have {n_out} features which is too large to be"
            f" indexed by {np.intp().dtype.name}."
        )
        raise ValueError(msg)

    ids = np.array(
        list(
            combinations_with_replacement(
                range(n_features + 1),
                degree,
            )
        )
    )

    const_id = np.where((ids == 0).all(axis=1))
    return np.delete(ids, const_id, 0)  # remove the constant featrue


class TimeShift(BaseEstimator, TransformerMixin):
    """Time shift features

    Parameters
    ----------
    ids : array-like of shape (`n_output_features_`, 2)
        The unique id numbers of output features, which are
        (feature_idx, delay).

    Attributes
    ----------
    n_features_in_ : int
        The number of input variables seen during :term:`fit`,
        which should be one.

    n_output_features_ : int
        The total number of polynomial output features.
    """

    _parameter_constraints: dict = {
        "ids": ["array-like"],
    }

    def __init__(self, ids):
        self.ids = ids

    def fit(self, X, y=None):
        """Compute number of output features.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            Fitted transformer.
        """
        self._validate_params()
        self.ids = check_array(array=self.ids, ensure_2d=True, dtype=int)
        if np.any(self.ids < 0):
            raise ValueError(
                "The ids should be formed with the number larger than or equal to 0."
            )

        n_samples, n_features = self._validate_data(X=X, reset=True).shape
        n_in = max(self.ids[:, 0]) + 1
        max_delay = max(self.ids[:, 1])
        if n_in > n_features:
            raise ValueError(
                "The number of features in ids (n_in) should be less than "
                "or equal to the number of features in X (n_features). Got "
                f"n_in={n_in} and n_features={n_features}."
            )
        if max_delay >= n_samples:
            raise ValueError(
                "The maximum time delay in ids should be less than "
                "the number of samples in X. Got "
                f"max_delay={max_delay} and n_samples={n_samples}."
            )

        self.n_output_features_ = self.ids.shape[0]

        return self

    def transform(self, X):
        """To generate feature with time shift.

        Parameters
        ----------
        X : array-likeof shape (n_samples, n_features)
            The data to transform, column by column.

        Returns
        -------
        out : ndarray of shape (n_samples, n_out)
            The matrix of features, where `n_out` is the number of time shift
            features generated from the combination of inputs.
        """
        check_is_fitted(self)
        ids = self.ids

        X = self._validate_data(X, reset=False)
        n_samples = X.shape[0]
        out = np.zeros([n_samples, self.n_output_features_])
        for i, id_temp in enumerate(ids):
            out[:, i] = np.r_[
                np.full(id_temp[1], X[0, id_temp[0]]),
                X[: -id_temp[1] or None, id_temp[0]],
            ]

        return out


class PolyBasis(BaseEstimator, TransformerMixin):
    """Poly basis function

    Parameters
    ----------
    ids : array-like of shape (`n_output_features_`, degree)
        The unique id numbers of output features, which are formed
        of non-negative int values.

    Attributes
    ----------
    n_features_in_ : int
        The number of input variables seen during :term:`fit`.

    n_output_features_ : int
        The total number of polynomial output features.


    """

    _parameter_constraints: dict = {
        "ids": ["array-like"],
    }

    def __init__(self, ids):
        self.ids = ids

    def fit(self, X, y=None):
        """Compute number of output features.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            Fitted transformer.
        """
        self._validate_params()
        self.ids = check_array(array=self.ids, ensure_2d=True, dtype=int)
        if (self.ids < 0).any():
            raise ValueError(
                f"The `ids` should be non-negative int, but got ids={self.ids}."
            )

        n_features = self._validate_data(X=X, reset=True).shape[1]
        n_out = self.ids.shape[0]
        n_in = np.abs(self.ids).max()
        if n_in > n_features:
            raise ValueError(
                "The number of features in ids (n_in) should be less than "
                "or equal to the number of features in X (n_features). Got "
                f"n_in={n_in} and n_features={n_features}."
            )

        self.n_output_features_ = n_out

        return self

    def transform(self, X):
        """To nonlinearise the variables by polynomial basis function

        Parameters
        ----------
        X : array-likeof shape (n_samples, n_features)
            The data to transform, column by column.

        Returns
        -------
        out.T : ndarray of shape (n_samples, n_out)
            The matrix of features, where `n_out` is the number of polynomial
            features generated from the combination of inputs.
        """
        check_is_fitted(self)
        ids = self.ids

        X = self._validate_data(X, reset=False)

        n_samples = X.shape[0]
        n_out, degree = ids.shape

        # Generate polynomial features
        out = np.ones([n_out, n_samples])
        unique_features = np.unique(ids)
        unique_features = unique_features[unique_features != 0]
        for i in range(degree):
            for j in unique_features:
                mask = ids[:, i] == j
                out[mask, :] *= X[:, j - 1]

        return out.T


class RadialBasis(BaseEstimator, TransformerMixin):
    """Radial basis function

    Parameters
    ----------
    ids : array-like of shape (`n_output_features_`, `n_features_in_`)
        The unique id numbers of output features.
        Each row of ids is a RBF center.

    length_scale : float, default=1.0
        The length scale of the radial basis. The length scale is used to
        form an isotropic kernel.

    Attributes
    ----------
    n_features_in_ : int
        The number of input variables seen during :term:`fit`.

    n_output_features_ : int
        The total number of polynomial output features.


    """

    _parameter_constraints: dict = {
        "ids": ["array-like"],
        "length_scale": [Interval(Real, 0, None, closed="neither")],
    }

    def __init__(self, ids, length_scale=1.0):
        self.ids = ids
        self.length_scale = length_scale

    def fit(self, X, y=None):
        """Compute number of output features.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            Fitted transformer.
        """
        self._validate_params()
        self.ids = check_array(array=self.ids, ensure_2d=True, dtype=int)
        n_features = self._validate_data(X=X, reset=True).shape[1]
        n_out = self.ids.shape[0]
        n_in = self.ids.shape[1]

        if n_in != n_features:
            raise ValueError(
                "The number of features in ids (n_in) should be equal to"
                "the number of features in X (n_features). Got "
                f"n_in={n_in} and n_features={n_features}."
            )

        self.n_output_features_ = n_out

        return self

    def transform(self, X):
        """To nonlinearise the variables by radial basis function

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The data to transform via RBF centers and length scales.

        Returns
        -------
        out : ndarray of shape (n_samples, n_out)
            The matrix of features, where `n_out` is the number of radial
            features generated from the sqared euclidean between inputs
            and RBF centers.
        """
        check_is_fitted(self)
        ids = self.ids

        X = self._validate_data(X, reset=False)

        sigma2 = self.length_scale**2
        # Generate RBF features
        dists = cdist(X, ids, "sqeuclidean")
        out = np.exp(-0.5 * dists / sigma2)
        return out

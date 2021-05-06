import numpy as np

from sklearn.metrics import pairwise_distances
from ITMO_FS.utils.information_theory import entropy, joint_entropy
from ITMO_FS.utils.information_theory import mutual_information
from ...utils import BaseTransformer, generate_features


def _complementarity(x_i, x_j, y):
    return (entropy(x_i) + entropy(x_j) + entropy(y) - joint_entropy(x_i, x_j) - 
           joint_entropy(x_i, y) - joint_entropy(x_j, y) + 
           joint_entropy(x_i, x_j, y))


def _chained_information(x_i, x_j, y):
    return (mutual_information(x_i, y) + mutual_information(x_j, y) + 
        _complementarity(x_i, x_j, y))


class DISRWithMassive(BaseTransformer):
    """
    Creates DISR (Double Input Symmetric Relevance) feature selection filter
    based on kASSI criterin for feature selection which aims at maximizing
    the mutual information avoiding, meanwhile, large multivariate density
    estimation. Its a kASSI criterion with approximation of the information
    of a set of variables by counting average information of subset on
    combination of two features. This formulation thus deals with feature
    complementarity up to order two by preserving the same computational
    complexity of the MRMR and CMIM criteria The DISR calculation is done
    using graph based solution.

        Parameters
        ----------
        n_features : int
            Number of features to select.

        Notes
        -----
        For more details see `this paper
        <http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.318.6576&rep=rep1&type=pdf/>`_.

        Examples
        --------
        >>> from ITMO_FS.filters.multivariate import DISRWithMassive
        >>> import numpy as np
        >>> X = np.array([[1, 2, 3, 3, 1],[2, 2, 3, 3, 2], [1, 3, 3, 1, 3], \
[3, 1, 3, 1, 4],[4, 4, 3, 1, 5]], dtype = np.integer)
        >>> y = np.array([1, 2, 3, 4, 5], dtype=np.integer)
        >>> disr = DISRWithMassive(3).fit(X, y)
        >>> disr.selected_features_
        array([0, 1, 4])
    """

    def __init__(self, n_features):
        super().__init__()
        self.n_features = n_features

    def _fit(self, x, y):
        """
            Fits filter

            Parameters
            ----------
            x : array-like, shape (n_samples, n_features)
                The training input samples.
            y : array-like, shape (n_samples, )
                The target values.

            Returns
            -------
            None
        """

        if self.n_features > self.n_features_:
            raise ValueError(
                "Cannot select %d features with n_features = %d" %
                (self.n_features, self.n_features_))

        free_features = np.array([], dtype='int')
        self.selected_features_ = generate_features(x)
        self._edges = pairwise_distances(x.T, x.T, lambda xi, xj: 
            _chained_information(xi, xj, y) / (joint_entropy(xi, xj) + 1e-15))
        np.fill_diagonal(self._edges, 0)
    
        while len(self.selected_features_) != self.n_features:
            min_index = np.argmin(np.sum(
                self._edges[np.ix_(self.selected_features_, 
                    self.selected_features_)], 
                axis=0))
            free_features = np.append(free_features, 
                self.selected_features_[min_index])
            self.selected_features_ = np.delete(
                self.selected_features_, min_index)

        while True:
            selected_weights = np.sum(self._edges[np.ix_(self.selected_features_, 
                    self.selected_features_)], axis=0)
            free_weights = np.sum(self._edges[np.ix_(self.selected_features_, 
                    free_features)], axis=0)
            difference = (free_weights.reshape(-1, 1) - self._edges[np.ix_(
                free_features, self.selected_features_)] - selected_weights)
            if np.all(difference <= 0):
                break
            index_add, index_del = np.unravel_index(np.argmax(difference), 
                difference.shape)
            self.selected_features_[index_del], free_features[index_add] = (
                free_features[index_add], self.selected_features_[index_del])

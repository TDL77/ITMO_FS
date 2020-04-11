from .measures import GLOB_MEASURE
from ...utils import generate_features

import numpy as np

class MultivariateFilter(object):
	"""
        Provides basic functionality for multivariate filters.

        Parameters
        ----------
        measure : string or callable
            A metric name defined in GLOB_MEASURE or a callable with signature measure(selected_features, dataset_with_features_left, labels)
            which should return a list of metric values for each feature in the dataset.
        n_features : int
            Number of features to select.

        See Also
        --------


        examples
        --------

    """
	def __init__(self, measure, n_features):
        
        if type(measure) is str:
            try:
                self.measure = GLOB_MEASURE[measure]
            except KeyError:
                raise KeyError("No %r measure yet" % measure)
        else:
            self.measure = measure

        self.__n_features = n_features
        self.selected_features = []

    def fit(self, X, y):
    	"""
            Fits the filter.

            Parameters
            ----------
            X : array-like, shape (n_features,n_samples)
                The training input samples.
            y : array-like, shape (n_features,n_samples)
                The target values.

            Returns
            ------
            None

            See Also
            --------

            examples
            --------
            from ITMO_FS.wrappers import SequentialForwardSelection
            from sklearn.datasets import make_classification

            import numpy as np

            dataset = make_classification(n_samples=100, n_features=20, n_informative=4, n_redundant=0, shuffle=False)
            data, target = np.array(dataset[0]), np.array(dataset[1])
            model = MultivariateFilter('MIM', 5)
            model.fit(data, target)
            print(model.selected_features)


        """
        features_left = generate_features(X)
        while len(self.selected_features) != self.__n_features:
        	values = self.measure(self.selected_features, X[:, features_left], y)
        	to_add = np.argmax(values)
        	self.selected_features = np.append(self.selected_features, features_left[to_add])
            features_left = np.delete(features_left, to_add)

    def transform(self, X):
        return X[:, self.selected_features]
class OneHotEncoder:
    """Simple One-Hot-Encoding for python lists. Uses a list of possible values for a one-hot encoding of a single
    value. The translated values must support ``__eq__()`` operator. The list of possible values must be set beforehand.
    Is used as a basic encoder example for ``MolecularGraphRDKit``. There can not be different dtypes in categories.
    """
    _dtype_translate = {"int": int, "float": float, "str": str}

    def __init__(self, categories: list, add_unknown: bool = True, dtype: str = "int"):
        """Initialize the encoder beforehand with a set of all possible values to encounter.

        Args:
            categories (list): List of possible values, matching the one-hot encoding.
            add_unknown (bool): Whether to add a unknown bit. Default is True.
        """
        assert isinstance(dtype, str)
        if dtype not in ["str", "int", "float"]:
            raise ValueError("Unsupported dtype for OneHotEncoder %s" % dtype)
        self.dtype_identifier = dtype
        self.dtype = self._dtype_translate[dtype]
        self.categories = [self.dtype(x) for x in categories]
        self.found_values = []
        self.add_unknown = add_unknown

    def __call__(self, value, **kwargs):
        r"""Encode a single feature or value, mapping it to a one-hot python list. E.g. `[0, 0, 1, 0]`

        Args:
            value: Any object that can be compared to items in ``self.one_hot_values``.
            **kwargs: Additional kwargs. Not used atm.

        Returns:
            list: Python list with 1 at value match. E.g. `[0, 0, 1, 0]`
        """
        encoded_list = [1 if x == self.dtype(value) else 0 for x in self.categories]
        if self.add_unknown:
            if value not in self.categories:
                encoded_list += [1]
            else:
                encoded_list += [0]
        if value not in self.found_values:
            self.found_values += [value]
        return encoded_list

    def get_config(self):
        config = {"categories": self.categories, "add_unknown": self.add_unknown, "dtype": self.dtype_identifier}
        return config

    @classmethod
    def from_config(cls, config):
        return cls(**config)
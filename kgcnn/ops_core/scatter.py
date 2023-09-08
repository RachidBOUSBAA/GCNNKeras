import kgcnn.backend as kgcnn_backend
from keras_core.backend import KerasTensor
from keras_core.backend import any_symbolic_tensors
from keras_core.ops.operation import Operation


class ScatterMax(Operation):
    def call(self, indices, values, shape):
        return kgcnn_backend.scatter_reduce_max(indices, values, shape)

    def compute_output_spec(self, indices, values, shape):
        return KerasTensor(shape, dtype=values.dtype)


def scatter_reduce_max(indices, values, shape):
    if any_symbolic_tensors((indices, values, shape)):
        return ScatterMax().symbolic_call(indices, values, shape)
    return kgcnn_backend.scatter_reduce_max(indices, values, shape)


class ScatterMin(Operation):
    def call(self, indices, values, shape):
        return kgcnn_backend.scatter_reduce_min(indices, values, shape)

    def compute_output_spec(self, indices, values, shape):
        return KerasTensor(shape, dtype=values.dtype)


def scatter_reduce_min(indices, values, shape):
    if any_symbolic_tensors((indices, values, shape)):
        return ScatterMin().symbolic_call(indices, values, shape)
    return kgcnn_backend.scatter_reduce_min(indices, values, shape)


class ScatterMean(Operation):
    def call(self, indices, values, shape):
        return kgcnn_backend.scatter_reduce_mean(indices, values, shape)

    def compute_output_spec(self, indices, values, shape):
        return KerasTensor(shape, dtype=values.dtype)


def scatter_reduce_mean(indices, values, shape):
    if any_symbolic_tensors((indices, values, shape)):
        return ScatterMean().symbolic_call(indices, values, shape)
    return kgcnn_backend.scatter_reduce_mean(indices, values, shape)


class ScatterSum(Operation):
    def call(self, indices, values, shape):
        return kgcnn_backend.scatter_reduce_sum(indices, values, shape)

    def compute_output_spec(self, indices, values, shape):
        return KerasTensor(shape, dtype=values.dtype)


def scatter_reduce_sum(indices, values, shape):
    if any_symbolic_tensors((indices, values, shape)):
        return ScatterSum().symbolic_call(indices, values, shape)
    return kgcnn_backend.scatter_reduce_sum(indices, values, shape)


class ScatterSoftmax(Operation):
    def call(self, indices, values, attention, shape):
        return kgcnn_backend.scatter_reduce_softmax(indices, values, attention, shape)

    def compute_output_spec(self, indices, values, attention, shape):
        return KerasTensor(shape, dtype=values.dtype)


def scatter_reduce_softmax(indices, values, attention, shape):
    if any_symbolic_tensors((indices, values, attention, shape)):
        return ScatterSoftmax().symbolic_call(indices, values, attention, shape)
    return kgcnn_backend.scatter_reduce_softmax(indices, values, attention, shape)
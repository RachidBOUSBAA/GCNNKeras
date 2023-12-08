# import keras_core as ks
from ._model import model_disjoint
from kgcnn.models.utils import update_model_kwargs
from kgcnn.layers.scale import get as get_scaler
from kgcnn.layers.modules import Input
from kgcnn.models.casting import template_cast_output, template_cast_list_input
from keras.backend import backend as backend_to_use
from kgcnn.ops.activ import *

# Keep track of model version from commit date in literature.
# To be updated if model is changed in a significant way.
__model_version__ = "2023-10-12"

# Supported backends
__kgcnn_model_backend_supported__ = ["tensorflow", "torch", "jax"]
if backend_to_use() not in __kgcnn_model_backend_supported__:
    raise NotImplementedError("Backend '%s' for model 'rGIN' is not supported." % backend_to_use())

# Implementation of rGIN in `keras` from paper:
# Random Features Strengthen Graph Neural Networks
# Ryoma Sato, Makoto Yamada, Hisashi Kashima
# https://arxiv.org/abs/2002.03155

model_default = {
    "name": "rGIN",
    "inputs": [
        {"shape": (None,), "name": "node_attributes", "dtype": "float32", "ragged": True},
        {"shape": (None, 2), "name": "edge_indices", "dtype": "int64", "ragged": True}
    ],
    "input_tensor_type": "padded",
    "cast_disjoint_kwargs": {},
    "input_embedding": None,  # deprecated
    "input_node_embedding": {"input_dim": 95, "output_dim": 64},
    "gin_mlp": {"units": [64, 64], "use_bias": True, "activation": ["relu", "linear"],
                "use_normalization": True, "normalization_technique": "graph_batch"},
    "rgin_args": {"random_range": 100},
    "depth": 3, "dropout": 0.0, "verbose": 10,
    "last_mlp": {"use_bias": [True, True, True], "units": [64, 64, 64],
                 "activation": ["relu", "relu", "linear"]},
    "output_embedding": 'graph',
    "output_mlp": {"use_bias": True, "units": 1,
                   "activation": "softmax"},
    "output_to_tensor": None,  # deprecated
    "output_tensor_type": "padded",
    "output_scaling": None,
}


@update_model_kwargs(model_default, update_recursive=0, deprecated=["input_embedding", "output_to_tensor"])
def make_model(inputs: list = None,
               input_tensor_type: str = None,
               cast_disjoint_kwargs: dict = None,
               input_embedding: dict = None,  # noqa
               input_node_embedding: dict = None,
               depth: int = None,
               rgin_args: dict = None,
               gin_mlp: dict = None,
               last_mlp: dict = None,
               dropout: float = None,
               name: str = None,  # noqa
               verbose: int = None,  # noqa
               output_embedding: str = None,
               output_to_tensor: bool = None,  # noqa
               output_mlp: dict = None,
               output_scaling: dict = None,
               output_tensor_type: str = None,
               ):
    r"""Make `rGIN <https://arxiv.org/abs/2002.03155>`__ graph network via functional API.
    Default parameters can be found in :obj:`kgcnn.literature.rGIN.model_default` .



    Args:
        inputs (list): List of dictionaries unpacked in :obj:`tf.keras.layers.Input`. Order must match model definition.
        input_tensor_type (str): Input type of graph tensor. Default is "padded".
        cast_disjoint_kwargs (dict): Dictionary of arguments for castin layers.
        input_embedding (dict): Deprecated in favour of input_node_embedding etc.
        input_node_embedding (dict): Dictionary of arguments for nodes unpacked in :obj:`Embedding` layers.
        depth (int): Number of graph embedding units or depth of the network.
        rgin_args (dict): Dictionary of layer arguments unpacked in :obj:`GIN` convolutional layer.
        gin_mlp (dict): Dictionary of layer arguments unpacked in :obj:`MLP` for convolutional layer.
        last_mlp (dict): Dictionary of layer arguments unpacked in last :obj:`MLP` layer before output or pooling.
        dropout (float): Dropout to use.
        name (str): Name of the model.
        verbose (int): Level of print output.
        output_embedding (str): Main embedding task for graph network. Either "node", "edge" or "graph".
        output_to_tensor (bool): Deprecated in favour of `output_tensor_type` .
        output_mlp (dict): Dictionary of layer arguments unpacked in the final classification :obj:`MLP` layer block.
            Defines number of model outputs and activation.
        output_scaling (dict): Dictionary of layer arguments unpacked in scaling layers. Default is None.
        output_tensor_type (str): Output type of graph tensors such as nodes or edges. Default is "padded".

    Returns:
        :obj:`keras.models.Model`
    """
    # Make input
    # Make input
    model_inputs = [Input(**x) for x in inputs]

    disjoint_inputs = template_cast_list_input(
        model_inputs, input_tensor_type=input_tensor_type, cast_disjoint_kwargs=cast_disjoint_kwargs,
        mask_assignment=[0, 1],
        index_assignment=[None, 0]
    )

    n, disjoint_indices, batch_id_node, batch_id_edge, node_id, edge_id, count_nodes, count_edges = disjoint_inputs

    # Wrapping disjoint model.
    out = model_disjoint(
        [n, disjoint_indices, batch_id_node, count_nodes],
        use_node_embedding=("int" in inputs[0]['dtype']) if input_node_embedding is not None else False,
        input_node_embedding=input_node_embedding,
        gin_mlp=gin_mlp,
        depth=depth,
        rgin_args=rgin_args,
        last_mlp=last_mlp,
        output_mlp=output_mlp,
        output_embedding=output_embedding,
        dropout=dropout
    )

    if output_scaling is not None:
        scaler = get_scaler(output_scaling["name"])(**output_scaling)
        out = scaler(out)

    # Output embedding choice
    out = template_cast_output(
        [out, batch_id_node, batch_id_edge, node_id, edge_id, count_nodes, count_edges],
        output_embedding=output_embedding, output_tensor_type=output_tensor_type,
        input_tensor_type=input_tensor_type, cast_disjoint_kwargs=cast_disjoint_kwargs
    )

    model = ks.models.Model(inputs=model_inputs, outputs=out, name=name)
    model.__kgcnn_model_version__ = __model_version__

    if output_scaling is not None:
        def set_scale(*args, **kwargs):
            scaler.set_scale(*args, **kwargs)

        setattr(model, "set_scale", set_scale)
    return model


make_model.__doc__ = make_model.__doc__ % (template_cast_list_input.__doc__, template_cast_output.__doc__)
from ._model import model_disjoint
from kgcnn.models.utils import update_model_kwargs
from kgcnn.layers.scale import get as get_scaler
from kgcnn.layers.modules import Input
from keras.backend import backend as backend_to_use
from kgcnn.models.casting import template_cast_list_input, template_cast_output
from kgcnn.ops.activ import *

# Keep track of model version from commit date in literature.
# To be updated if model is changed in a significant way.
__model_version__ = "2023-12-08"

# Supported backends
__kgcnn_model_backend_supported__ = ["tensorflow", "torch", "jax"]
if backend_to_use() not in __kgcnn_model_backend_supported__:
    raise NotImplementedError("Backend '%s' for model 'INorp' is not supported." % backend_to_use())

# Implementation of INorp in `tf.keras` from paper:
# 'Interaction Networks for Learning about Objects, Relations and Physics'
# by Peter W. Battaglia, Razvan Pascanu, Matthew Lai, Danilo Rezende, Koray Kavukcuoglu
# http://papers.nips.cc/paper/6417-interaction-networks-for-learning-about-objects-relations-and-physics
# https://arxiv.org/abs/1612.00222
# https://github.com/higgsfield/interaction_network_pytorch


model_default = {
    'name': "INorp",
    'inputs': [
        {'shape': (None,), 'name': "node_number", 'dtype': 'int64'},
        {'shape': (None,), 'name': "edge_number", 'dtype': 'int64'},
        {'shape': (None, 2), 'name': "edge_indices", 'dtype': 'int64'},
        {'shape': (64, ), 'name': "graph_attributes", 'dtype': 'float32'},
        {"shape": (), "name": "total_nodes", "dtype": "int64"},
        {"shape": (), "name": "total_edges", "dtype": "int64"}
    ],
    'input_embedding': None,
    "cast_disjoint_kwargs": {},
    "input_node_embedding": {"input_dim": 95, "output_dim": 64},
    "input_edge_embedding": {"input_dim": 5, "output_dim": 64},
    "input_graph_embedding": {"input_dim": 100, "output_dim": 64},
    "set2set_args": {
        "channels": 32, "T": 3, "pooling_method": "mean",
        "init_qstar": "mean"},
    'node_mlp_args': {"units": [100, 50], "use_bias": True, "activation": ['relu', "linear"]},
    'edge_mlp_args': {
        "units": [100, 100, 100, 100, 50],
        "activation": ['relu', 'relu', 'relu', 'relu', "linear"]},
    'pooling_args': {'pooling_method': "mean"},
    'depth': 3, 'use_set2set': False, 'verbose': 10,
    'gather_args': {},
    'output_embedding': 'graph',
    "output_to_tensor": None,  # deprecated
    "output_tensor_type": "padded",
    "output_scaling": None,
    'output_mlp': {
        "use_bias": [True, True, False], "units": [25, 10, 1],
        "activation": ['relu', 'relu', 'sigmoid']}
}


@update_model_kwargs(model_default, update_recursive=0, deprecated=["input_embedding", "output_to_tensor"])
def make_model(inputs: list = None,
               input_tensor_type: str = None,
               cast_disjoint_kwargs: dict = None,
               input_embedding: dict = None,  # noqa
               input_node_embedding: dict = None,
               input_edge_embedding: dict = None,
               input_graph_embedding: dict = None,
               depth: int = None,
               gather_args: dict = None,
               edge_mlp_args: dict = None,
               node_mlp_args: dict = None,
               set2set_args: dict = None,
               pooling_args: dict = None,
               use_set2set: dict = None,
               name: str = None,
               verbose: int = None,  # noqa
               output_embedding: str = None,
               output_to_tensor: bool = None,  # noqa
               output_mlp: dict = None,
               output_scaling: dict = None,
               output_tensor_type: str = None
               ):
    r"""Make `INorp <https://arxiv.org/abs/1612.00222>`__ graph network via functional API.
    Default parameters can be found in :obj:`kgcnn.literature.INorp.model_default` .

    **Model inputs**:
    Model uses the list template of inputs and standard output template.
    The supported inputs are  :obj:`[nodes, edges, edge_indices, graph_state, ...]`
    with '...' indicating mask or ID tensors following the template below.

    %s

    **Model outputs**:
    The standard output template:

    %s

    Args:
        inputs (list): List of dictionaries unpacked in :obj:`tf.keras.layers.Input`. Order must match model definition.
        input_tensor_type (str): Input type of graph tensor. Default is "padded".
        cast_disjoint_kwargs (dict): Dictionary of arguments for casting layer.
        input_embedding (dict): Deprecated in favour of input_node_embedding etc.
        input_node_embedding (dict): Dictionary of embedding arguments for nodes unpacked in :obj:`Embedding` layers.
        input_edge_embedding (dict): Dictionary of embedding arguments for nodes unpacked in :obj:`Embedding` layers.
        input_graph_embedding (dict): Dictionary of embedding arguments for graph unpacked in :obj:`Embedding` layers.
        depth (int): Number of graph embedding units or depth of the network.
        gather_args (dict): Dictionary of layer arguments unpacked in :obj:`GatherNodes` layer.
        edge_mlp_args (dict): Dictionary of layer arguments unpacked in :obj:`MLP` layer for edge updates.
        node_mlp_args (dict): Dictionary of layer arguments unpacked in :obj:`MLP` layer for node updates.
        set2set_args (dict): Dictionary of layer arguments unpacked in :obj:`PoolingSet2SetEncoder` layer.
        pooling_args (dict): Dictionary of layer arguments unpacked in :obj:`AggregateLocalEdges`, :obj:`PoolingNodes`
            layer.
        use_set2set (bool): Whether to use :obj:`PoolingSet2SetEncoder` layer.
        verbose (int): Level of verbosity.
        name (str): Name of the model.
        output_embedding (str): Main embedding task for graph network. Either "node", "edge" or "graph".
        output_scaling (dict): Dictionary of layer arguments unpacked in scaling layers. Default is None.
        output_tensor_type (str): Output type of graph tensors such as nodes or edges. Default is "padded".
        output_to_tensor (bool): Deprecated in favour of `output_tensor_type` .
        output_mlp (dict): Dictionary of layer arguments unpacked in the final classification :obj:`MLP` layer block.
            Defines number of model outputs and activation.

    Returns:
        :obj:`keras.models.Model`
    """
    # Make input
    model_inputs = [Input(**x) for x in inputs]

    di_inputs = template_cast_list_input(
        model_inputs,
        input_tensor_type=input_tensor_type,
        cast_disjoint_kwargs=cast_disjoint_kwargs,
        mask_assignment=[0, 1, 1, None],
        index_assignment=[None, None, 0, None]
    )

    n, ed, disjoint_indices, gs, batch_id_node, batch_id_edge, node_id, edge_id, count_nodes, count_edges = di_inputs

    # Wrapping disjoint model.
    out = model_disjoint(
        [n, ed, disjoint_indices, gs, batch_id_node, count_nodes],
        use_node_embedding=("int" in inputs[0]['dtype']) if input_node_embedding is not None else False,
        use_edge_embedding=("int" in inputs[1]['dtype']) if input_edge_embedding is not None else False,
        use_graph_embedding=("int" in inputs[3]['dtype']) if input_graph_embedding is not None else False,
        input_node_embedding=input_node_embedding,
        input_edge_embedding=input_edge_embedding,
        input_graph_embedding=input_graph_embedding,
        gather_args=gather_args,
        depth=depth,
        edge_mlp_args=edge_mlp_args,
        pooling_args=pooling_args,
        node_mlp_args=node_mlp_args,
        output_embedding=output_embedding,
        use_set2set=use_set2set,
        set2set_args=set2set_args,
        output_mlp=output_mlp
    )

    if output_scaling is not None:
        scaler = get_scaler(output_scaling["name"])(**output_scaling)
        out = scaler(out)

    # Output embedding choice
    out = template_cast_output(
        [out, batch_id_node, batch_id_edge, node_id, edge_id, count_nodes, count_edges],
        output_embedding=output_embedding, output_tensor_type=output_tensor_type,
        input_tensor_type=input_tensor_type, cast_disjoint_kwargs=cast_disjoint_kwargs,
    )

    model = ks.models.Model(inputs=model_inputs, outputs=out, name=name)
    model.__kgcnn_model_version__ = __model_version__

    if output_scaling is not None:
        def set_scale(*args, **kwargs):
            scaler.set_scale(*args, **kwargs)

        setattr(model, "set_scale", set_scale)

    return model


make_model.__doc__ = make_model.__doc__ % (template_cast_list_input.__doc__, template_cast_output.__doc__)
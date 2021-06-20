import tensorflow as tf

from kgcnn.layers.base import GraphBaseLayer
from kgcnn.ops.partition import change_row_index_partition


@tf.keras.utils.register_keras_serializable(package='kgcnn', name='GatherNodes')
class GatherNodes(GraphBaseLayer):
    """Gather nodes by indices, e.g. that define an edge.

    An edge is defined by index tuple (i,j) with i<-j connection.
    If graphs indices were in 'batch' mode, the layer's 'node_indexing' must be set to 'batch'.
    """

    def __init__(self,
                 concat_nodes=True,
                 **kwargs):
        """Initialize layer."""
        super(GatherNodes, self).__init__(**kwargs)
        self.concat_nodes = concat_nodes

    def build(self, input_shape):
        """Build layer."""
        super(GatherNodes, self).build(input_shape)

    def call(self, inputs, **kwargs):
        """Forward pass.

        Args:
            inputs (list): [nodes, tensor_index]

                - nodes (tf.RaggedTensor): Node embeddings of shape (batch, [N], F)
                - tensor_index (tf.RaggedTensor): Edge indices referring to nodes of shape (batch, [M], 2)

        Returns:
            tf.RaggedTensor: Gathered node embeddings that match the number of edges.
        """
        dyn_inputs = inputs
        # We cast to values here
        node, node_part = dyn_inputs[0].values, dyn_inputs[0].row_splits
        edge_index, edge_part = dyn_inputs[1].values, dyn_inputs[1].row_lengths()

        indexlist = change_row_index_partition(edge_index, node_part, edge_part,
                                               partition_type_target="row_splits",
                                               partition_type_index="row_length",
                                               to_indexing='batch',
                                               from_indexing=self.node_indexing)
        out = tf.gather(node, indexlist, axis=0)
        if self.concat_nodes:
            out = tf.keras.backend.concatenate([out[:, i] for i in range(edge_index.shape[-1])], axis=1)
        # For ragged tensor we can now also try:
        # out = tf.gather(nod, tensor_index, batch_dims=1) # Works now
        # if self.concat_nodes:
        #   out = tf.keras.backend.concatenate([out[:, :, i] for i in range(tensor_index.shape[-1])], axis=2)
        out = tf.RaggedTensor.from_row_lengths(out, edge_part, validate=self.ragged_validate)
        return out

    def get_config(self):
        """Update config."""
        config = super(GatherNodes, self).get_config()
        config.update({"concat_nodes": self.concat_nodes})
        return config


@tf.keras.utils.register_keras_serializable(package='kgcnn', name='GatherNodesOutgoing')
class GatherNodesOutgoing(GraphBaseLayer):
    """Gather nodes by indices.

    For outgoing nodes, layer uses only index[1]. An edge is defined by index tuple (i,j) with i<-j connection.
    If graphs indices were in 'batch' mode, the layer's 'node_indexing' must be set to 'batch'.
    """

    def __init__(self, **kwargs):
        """Initialize layer."""
        super(GatherNodesOutgoing, self).__init__(**kwargs)

    def build(self, input_shape):
        """Build layer."""
        super(GatherNodesOutgoing, self).build(input_shape)

    def call(self, inputs, **kwargs):
        """Forward pass.

        Args:
            inputs (list): [nodes, tensor_index]

                - nodes (tf.RaggedTensor): Node embeddings of shape (batch, [N], F)
                - tensor_index (tf.RaggedTensor): Edge indices referring to nodes of shape (batch, [M], 2)

        Returns:
            tf.RaggedTensor: Gathered node embeddings that match the number of edges of shape (batch, [M], F)
        """
        dyn_inputs = inputs

        # We cast to values here
        node, node_part = dyn_inputs[0].values, dyn_inputs[0].row_splits
        edge_index, edge_part = dyn_inputs[1].values, dyn_inputs[1].row_lengths()

        indexlist = change_row_index_partition(edge_index, node_part, edge_part,
                                               partition_type_target="row_splits",
                                               partition_type_index="row_length",
                                               to_indexing='batch',
                                               from_indexing=self.node_indexing)
        # For ragged tensor we can now also try:
        # out = tf.gather(nod, tensor_index[:, :, 1], batch_dims=1)
        out = tf.gather(node, indexlist[:, 1], axis=0)

        out = tf.RaggedTensor.from_row_lengths(out, edge_part, validate=self.ragged_validate)
        return out

    def get_config(self):
        """Update config."""
        config = super(GatherNodesOutgoing, self).get_config()
        return config


@tf.keras.utils.register_keras_serializable(package='kgcnn', name='GatherNodesIngoing')
class GatherNodesIngoing(GraphBaseLayer):
    """Gather nodes by edge edge_indices.
    
    For ingoing nodes, layer uses only index[0]. An edge is defined by index tuple (i,j) with i<-j connection.
    If graphs indices were in 'batch' mode, the layer's 'node_indexing' must be set to 'batch'.
    """

    def __init__(self, **kwargs):
        """Initialize layer."""
        super(GatherNodesIngoing, self).__init__(**kwargs)

    def build(self, input_shape):
        """Build layer."""
        super(GatherNodesIngoing, self).build(input_shape)

    def call(self, inputs, **kwargs):
        """Forward pass.

        Args:
            inputs (list): [nodes, tensor_index]

                - nodes (tf.RaggedTensor): Node embeddings of shape (batch, [N], F)
                - tensor_index (tf.RaggedTensor): Edge indices referring to nodes of shape (batch, [M], 2)

        Returns:
            tf.RaggedTensor: Gathered node embeddings that match the number of edges of shape (batch, [M], F)
        """
        dyn_inputs = inputs

        # We cast to values here
        node, node_part = dyn_inputs[0].values, dyn_inputs[0].row_splits
        edge_index, edge_part = dyn_inputs[1].values, dyn_inputs[1].row_lengths()

        # We cast to values here
        indexlist = change_row_index_partition(edge_index, node_part, edge_part,
                                               partition_type_target="row_splits",
                                               partition_type_index="row_length",
                                               to_indexing='batch',
                                               from_indexing=self.node_indexing)
        out = tf.gather(node, indexlist[:, 0], axis=0)
        # For ragged tensor we can now also try:
        # out = tf.gather(nod, tensor_index[:, :, 0], batch_dims=1)
        out = tf.RaggedTensor.from_row_lengths(out, edge_part, validate=self.ragged_validate)
        return out

    def get_config(self):
        """Update config."""
        config = super(GatherNodesIngoing, self).get_config()
        return config


@tf.keras.utils.register_keras_serializable(package='kgcnn', name='GatherState')
class GatherState(GraphBaseLayer):
    """Layer to repeat environment or global state for node or edge lists.
    
    To repeat the correct environment for each sample, a tensor with the target length/partition is required.
    """

    def __init__(self, **kwargs):
        """Initialize layer."""
        super(GatherState, self).__init__(**kwargs)

    def build(self, input_shape):
        """Build layer."""
        super(GatherState, self).build(input_shape)

    def call(self, inputs, **kwargs):
        """Forward pass.

        Args:
            inputs: [state, target]

                - state (tf.Tensor): Graph specific embedding tensor. This is tensor of shape (batch, F)
                - target (tf.RaggedTensor): Target to collect state for, of shape (batch, [N], F)

        Returns:
            tf.RaggedTensor: Graph embedding with repeated single state for each graph of shape (batch, [N], F).
        """
        dyn_inputs = inputs[1]

        # We cast to values here
        env = inputs[0]
        target_len = dyn_inputs.row_lengths()

        out = tf.repeat(env, target_len, axis=0)
        out = tf.RaggedTensor.from_row_lengths(out, target_len, validate=self.ragged_validate)
        return out

    def get_config(self):
        """Update config."""
        config = super(GatherState, self).get_config()
        return config

hyper = {
    "GATv2": {
        "model": {
            "class_name": "make_model",
            "module_name": "kgcnn.literature_core.GATv2",
            "config": {
                "name": "GATv2",
                "inputs": [
                    {"shape": [None, 1433], "name": "node_attributes", "dtype": "float32"},
                    {"shape": [None, 1], "name": "edge_weights", "dtype": "float32"},
                    {"shape": [None, 2], "name": "edge_indices", "dtype": "int64"},
                    {"shape": (), "name": "total_nodes", "dtype": "int64"},
                    {"shape": (), "name": "total_edges", "dtype": "int64"}
                ],
                "cast_disjoint_kwargs": {},
                "input_node_embedding": {"input_dim": 95, "output_dim": 64},
                "input_edge_embedding": {"input_dim": 8, "output_dim": 64},
                "attention_args": {"units": 32, "use_bias": True, "use_edge_features": True, "activation": "relu",
                                   "use_final_activation": False, "has_self_loops": True},
                "pooling_nodes_args": {"pooling_method": "scatter_mean"},
                "depth": 3, "attention_heads_num": 10,
                "attention_heads_concat": False, "verbose": 10,
                "output_embedding": "node",
                "output_mlp": {"use_bias": [True, True, False], "units": [64, 32, 7],
                               "activation": ["relu", "relu", "softmax"]},
            }
        },
        "training": {
            "fit": {
                "batch_size": 1,
                "epochs": 250,
                "validation_freq": 10,
                "verbose": 2,
                "callbacks": [
                    {"class_name": "kgcnn>LinearLearningRateScheduler", "config": {
                        "learning_rate_start": 1e-03, "learning_rate_stop": 1e-04,
                        "epo_min": 200, "epo": 250, "verbose": 0}
                     }
                ]
            },
            "compile": {
                "optimizer": {"class_name": "Adam", "config": {"learning_rate": 1e-03}},
                "loss": "categorical_crossentropy",
                "weighted_metrics": ["categorical_accuracy", {"class_name": "AUC", "config": {"name": "auc"}}]
            },
            "cross_validation": {"class_name": "KFold",
                                 "config": {"n_splits": 5, "random_state": 42, "shuffle": True}},
            "multi_target_indices": None
        },
        "data": {
            "dataset": {
                "class_name": "CoraLuDataset",
                "module_name": "kgcnn.data.datasets.CoraLuDataset",
                "config": {},
                "methods": [
                    {"map_list": {"method": "make_undirected_edges"}},
                    {"map_list": {"method": "add_edge_self_loops"}},
                    {"map_list": {"method": "normalize_edge_weights_sym"}},
                    {"map_list": {"method": "count_nodes_and_edges"}},
                ]
            },
        },
        "info": {
            "postfix": "",
            "postfix_file": "",
            "kgcnn_version": "4.0.0"
        }
    },
    "GAT": {
        "model": {
            "class_name": "make_model",
            "module_name": "kgcnn.literature_core.GAT",
            "config": {
                "name": "GAT",
                "inputs": [
                    {"shape": [None, 1433], "name": "node_attributes", "dtype": "float32"},
                    {"shape": [None, 1], "name": "edge_weights", "dtype": "float32"},
                    {"shape": [None, 2], "name": "edge_indices", "dtype": "int64"},
                    {"shape": (), "name": "total_nodes", "dtype": "int64"},
                    {"shape": (), "name": "total_edges", "dtype": "int64"}
                ],
                "cast_disjoint_kwargs": {},
                "input_node_embedding": {"input_dim": 95, "output_dim": 64},
                "input_edge_embedding": {"input_dim": 8, "output_dim": 64},
                "attention_args": {"units": 32, "use_bias": True, "use_edge_features": True,
                                   "activation": "relu",
                                   "use_final_activation": False, "has_self_loops": True},
                "pooling_nodes_args": {"pooling_method": "scatter_mean"},
                "depth": 1, "attention_heads_num": 10,
                "attention_heads_concat": False, "verbose": 10,
                "output_embedding": "node", "output_to_tensor": True,
                "output_mlp": {"use_bias": [True, True, False], "units": [64, 32, 7],
                               "activation": ["relu", "relu", "softmax"]},
            }
        },
        "training": {
            "fit": {
                "batch_size": 1,
                "epochs": 250,
                "validation_freq": 10,
                "verbose": 2,
                "callbacks": [
                    {"class_name": "kgcnn>LinearLearningRateScheduler", "config": {
                        "learning_rate_start": 1e-03, "learning_rate_stop": 1e-04,
                        "epo_min": 200, "epo": 250, "verbose": 0}
                    }
                ]
            },
            "compile": {
                "optimizer": {"class_name": "Adam", "config": {"learning_rate": 1e-03}},
                "loss": "categorical_crossentropy",
                "weighted_metrics": [
                    "categorical_accuracy",
                    {"class_name": "AUC", "config": {"name": "auc"}}
                ]
            },
            "cross_validation": {"class_name": "KFold",
                                 "config": {"n_splits": 5, "random_state": 42, "shuffle": True}},
            "multi_target_indices": None
        },
        "data": {
            "dataset": {
                "class_name": "CoraLuDataset",
                "module_name": "kgcnn.data.datasets.CoraLuDataset",
                "config": {},
                "methods": [
                    {"map_list": {"method": "make_undirected_edges"}},
                    {"map_list": {"method": "add_edge_self_loops"}},
                    {"map_list": {"method": "normalize_edge_weights_sym"}},
                    {"map_list": {"method": "count_nodes_and_edges"}},
                ]
            },
        },
        "info": {
            "postfix": "",
            "postfix_file": "",
            "kgcnn_version": "4.0.0"
        }
    },
    "GCN": {
        "model": {
            "class_name": "make_model",
            "module_name": "kgcnn.literature_core.GCN",
            "config": {
                "name": "GCN",
                "inputs": [
                    {"shape": [None, 1433], "name": "node_attributes", "dtype": "float32"},
                    {"shape": [None, 1], "name": "edge_weights", "dtype": "float32"},
                    {"shape": [None, 2], "name": "edge_indices", "dtype": "int64"},
                    {"shape": (), "name": "total_nodes", "dtype": "int64"},
                    {"shape": (), "name": "total_edges", "dtype": "int64"}
                ],
                "cast_disjoint_kwargs": {"padded_disjoint": False},
                "input_node_embedding": {"input_dim": 95, "output_dim": 64},
                "input_edge_embedding": {"input_dim": 25, "output_dim": 1},
                "gcn_args": {"units": 64, "use_bias": True, "activation": "relu"},
                "depth": 3, "verbose": 10,
                "output_embedding": "node",
                "output_to_tensor": True,
                "output_mlp": {"use_bias": [True, True, False], "units": [64, 32, 7],
                               "activation": ["relu", "relu", "softmax"]},
            }
        },
        "training": {
            "fit": {
                "batch_size": 1,
                "epochs": 300,
                "validation_freq": 10,
                "verbose": 2,
                "callbacks": [
                    {
                        "class_name": "kgcnn>LinearLearningRateScheduler", "config": {
                            "learning_rate_start": 1e-03, "learning_rate_stop": 1e-04, "epo_min": 260, "epo": 300,
                            "verbose": 0
                        }
                    }
                ]
            },
            "compile": {
                "optimizer": {"class_name": "Adam", "config": {"learning_rate": 1e-03}},
                "loss": "categorical_crossentropy",
                "weighted_metrics": ["categorical_accuracy", {"class_name": "AUC", "config":{"name": "auc"}}]
            },
            "cross_validation": {"class_name": "KFold",
                                 "config": {"n_splits": 5, "random_state": 42, "shuffle": True}},
            "multi_target_indices": None
        },
        "data": {
            "dataset": {
                "class_name": "CoraLuDataset",
                "module_name": "kgcnn.data.datasets.CoraLuDataset",
                "config": {},
                "methods": [
                    {"map_list": {"method": "make_undirected_edges"}},
                    {"map_list": {"method": "add_edge_self_loops"}},
                    {"map_list": {"method": "normalize_edge_weights_sym"}},
                    {"map_list": {"method": "count_nodes_and_edges"}},
                ]
            },
        },
        "info": {
            "postfix": "",
            "postfix_file": "",
            "kgcnn_version": "4.0.0"
        }
    },
    "GraphSAGE": {
        "model": {
            "class_name": "make_model",
            "module_name": "kgcnn.literature_core.GraphSAGE",
            "config": {
                "name": "GraphSAGE",
                "inputs": [
                    {"shape": [None, 1433], "name": "node_attributes", "dtype": "float32"},
                    {"shape": [None, 1], "name": "edge_weights", "dtype": "float32"},
                    {"shape": [None, 2], "name": "edge_indices", "dtype": "int64"},
                    {"shape": (), "name": "total_nodes", "dtype": "int64"},
                    {"shape": (), "name": "total_edges", "dtype": "int64"}
                ],
                "cast_disjoint_kwargs": {"padded_disjoint": False},
                "input_node_embedding": {"input_dim": 95, "output_dim": 64},
                "input_edge_embedding": {"input_dim": 25, "output_dim": 1},
                "node_mlp_args": {"units": [64, 32], "use_bias": True, "activation": ["relu", "linear"]},
                "edge_mlp_args": {"units": 64, "use_bias": True, "activation": "relu"},
                "pooling_args": {"pooling_method": "scatter_sum"},
                "gather_args": {},
                "concat_args": {"axis": -1},
                "use_edge_features": True,
                "pooling_nodes_args": {"pooling_method": "scatter_sum"},
                "depth": 3, "verbose": 10,
                "output_embedding": "node",
                "output_mlp": {"use_bias": [True, True, False], "units": [64, 32, 7],
                               "activation": ["relu", "relu", "softmax"]}
            }
        },
        "training": {
            "fit": {
                "batch_size": 1,
                "epochs": 500, "validation_freq": 10, "verbose": 2,
                "callbacks": [{"class_name": "kgcnn>LinearLearningRateScheduler",
                               "config": {"learning_rate_start": 0.5e-3, "learning_rate_stop": 1e-5,
                                   "epo_min": 400, "epo": 500, "verbose": 0}}]
            },
            "compile": {
                "optimizer": {"class_name": "Adam", "config": {"learning_rate": 5e-3}},
                "loss": "categorical_crossentropy",
                "weighted_metrics": ["categorical_accuracy", {"class_name": "AUC", "config": {"name": "auc"}}]
            },
            "cross_validation": {"class_name": "KFold",
                                 "config": {"n_splits": 5, "random_state": 42, "shuffle": True}},
            "multi_target_indices": None
        },
        "data": {
            "dataset": {
                "class_name": "CoraLuDataset",
                "module_name": "kgcnn.data.datasets.CoraLuDataset",
                "config": {},
                "methods": [
                    {"map_list": {"method": "make_undirected_edges"}},
                    {"map_list": {"method": "add_edge_self_loops"}},
                    {"map_list": {"method": "normalize_edge_weights_sym"}},
                    {"map_list": {"method": "count_nodes_and_edges"}}
                ]
            },
        },
        "info": {
            "postfix": "",
            "postfix_file": "",
            "kgcnn_version": "4.0.0"
        }
    },
    "GIN": {
        "model": {
            "class_name": "make_model",
            "module_name": "kgcnn.literature_core.GIN",
            "config": {
                "name": "GIN",
                "inputs": [
                    {"shape": [None, 1433], "name": "node_attributes", "dtype": "float32"},
                    {"shape": [None, 2], "name": "edge_indices", "dtype": "int64"},
                    {"shape": (), "name": "total_nodes", "dtype": "int64"},
                    {"shape": (), "name": "total_edges", "dtype": "int64"}
                ],
                "cast_disjoint_kwargs": {"padded_disjoint": False},
                "input_node_embedding": {"input_dim": 95, "output_dim": 64},
                "depth": 5,
                "dropout": 0.05,
                "gin_mlp": {"units": [64, 64], "use_bias": True, "activation": ["relu", "linear"],
                            "use_normalization": False},
                "gin_args": {},
                "last_mlp": {"use_bias": True, "units": [64, 32, 7], "activation": ["relu", "relu", "linear"]},
                "output_embedding": "node",
                "output_mlp": {"activation": "softmax", "units": 7}
            }
        },
        "training": {
            "fit": {"batch_size": 1,
                    "epochs": 500, "validation_freq": 10, "verbose": 2,
                    "callbacks": [{"class_name": "kgcnn>LinearLearningRateScheduler",
                                   "config": {"learning_rate_start": 0.5e-3, "learning_rate_stop": 1e-5,
                                   "epo_min": 400, "epo": 500, "verbose": 0}}]
            },
            "compile": {
                "optimizer": {"class_name": "Adam", "config": {"learning_rate": 5e-3}},
                "loss": "categorical_crossentropy",
                "weighted_metrics": ["categorical_accuracy", {"class_name": "AUC", "config": {"name": "auc"}}]
            },
            "cross_validation": {"class_name": "KFold",
                                 "config": {"n_splits": 5, "random_state": 42, "shuffle": True}},
            "multi_target_indices": None
        },
        "data": {
            "dataset": {
                "class_name": "CoraLuDataset",
                "module_name": "kgcnn.data.datasets.CoraLuDataset",
                "config": {},
                "methods": [
                    {"map_list": {"method": "make_undirected_edges"}},
                    {"map_list": {"method": "add_edge_self_loops"}},
                    {"map_list": {"method": "normalize_edge_weights_sym"}},
                    {"map_list": {"method": "count_nodes_and_edges"}},
                ]
            },
        },
        "info": {
            "postfix": "",
            "postfix_file": "",
            "kgcnn_version": "4.0.0"
        }
    },
}
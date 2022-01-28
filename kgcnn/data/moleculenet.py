import os
import numpy as np
import pandas as pd
import logging

from kgcnn.mol.gen.base import smile_to_mol
from kgcnn.data.base import MemoryGraphDataset
from kgcnn.utils.data import save_json_file, load_json_file
from kgcnn.mol.graphRD import MolecularGraphRDKit
from kgcnn.mol.enocder import OneHotEncoder
from kgcnn.mol.io import write_mol_block_list_to_sdf, read_mol_list_from_sdf_file
from kgcnn.utils.data import pandas_data_frame_columns_to_numpy


class MoleculeNetDataset(MemoryGraphDataset):
    r"""Class for using molecule datasets. The concept is to load a table of smiles and corresponding targets and
    convert them into a tensors representation for graph networks.

    The class provides properties and methods for making graph features from smiles.
    The typical input is a `csv` or `excel` file with smiles and corresponding graph labels.

    The graph structure matches the molecular graph, i.e. the chemical structure. The atomic coordinates
    are generated by a conformer guess. Since this require some computation time, it is only done once and the
    molecular coordinate or mol-blocks stored in a single SDF file with the base-name of the csv :obj:``file_name``.

    The selection of smiles and whether conformers should be generated is handled by sub-classes or specified in the
    the methods :obj:`prepare_data` and :obj:`read_in_memory`, see the documentation of the methods
    for further details.
    """

    def __init__(self, data_directory: str = None, dataset_name: str = None, file_name: str = None,
                 verbose: int = 10):
        r"""Initialize a `MoleculeNetDataset` with information of the dataset location on disk.

        Args:
            file_name (str): Filename for reading into memory. This must be the name of the '.csv' file.
                Default is None.
            data_directory (str): Full path to directory containing all dataset files. Default is None.
            dataset_name (str): Name of the dataset. Important for naming. Default is None.
            verbose (int): Logging level. Default is 10.
        """
        MemoryGraphDataset.__init__(self, data_directory=data_directory, dataset_name=dataset_name,
                                    file_name=file_name, verbose=verbose)

    @property
    def file_path_mol(self):
        """Try to determine a file path for the mol information to store."""
        return os.path.splitext(self.file_path)[0] + ".sdf"

    def _smiles_to_mol_list(self, smiles: list, add_hydrogen: bool = True, sanitize: bool = True,
                            make_conformers: bool = True, optimize_conformer: bool = True,
                            external_program: dict = None, num_workers: int = None):
        r"""Convert a list of smiles as string into a list of mol-information, namely mol-block as string.

        Args:
            smiles (list): A list of smiles for each molecule in dataset.
            add_hydrogen (bool): Whether to add hydrogen after smile translation.
            sanitize (bool): Whether to sanitize molecule.
            make_conformers (bool): Try to generate 3D coordinates
            optimize_conformer (bool): Whether to optimize conformer via force field.
                Only possible with :obj:`make_conformers`. Default is True.
            external_program (dict): External program for translating smiles. Default is None.
                If you want to use an external program you have to supply a dictionary of the form:
                {"class_name": "balloon", "config": {"balloon_executable_path": ..., ...}}.
                Note that usually the parameters like :obj:`add_hydrogen` are ignored. And you need to control the
                SDF file generation within `config` of the :obj:`external_program`.
            num_workers (int): Parallel execution for translating smiles.

        Returns:
            list: A list of mol-block information as sting.
        """
        if len(smiles) == 0:
            self.error("Can not translate smiles, received empty list for %s." % self.dataset_name)

        self.info("Generating molecules and store %s to disk..." % self.file_path_mol)
        molecule_list = []
        for i in range(0, len(smiles), 1000):
            mg = smile_to_mol(smiles[i:i+1000], self.data_directory,
                              add_hydrogen=add_hydrogen, sanitize=sanitize,
                              make_conformers=make_conformers, optimize_conformer=optimize_conformer,
                              external_program=external_program, num_workers=num_workers)
            molecule_list = molecule_list + mg
            self.info(" ... converted molecules {0} from {1}".format(i+len(mg), len(smiles)))

        return molecule_list

    def prepare_data(self, overwrite: bool = False, smiles_column_name: str = "smiles",
                     add_hydrogen: bool = True, sanitize: bool = True,
                     make_conformers: bool = True, optimize_conformer: bool = True,
                     external_program: dict = None, num_workers: int = None):
        r"""Pre-computation of molecular structure information and optionally conformers. This function reads smiles
        from the csv-file given by :obj:`file_name` and creates a SDF File of generated mol-blocks with the same
        file name. The class requires RDKit and OpenBabel.
        Smiles that are not compatible with both RDKit and OpenBabel result in an empty mol-block in the SDF file to
        keep the number of molecules the same.

        Args:
            overwrite (bool): Overwrite existing database mol-json file. Default is False.
            smiles_column_name (str): Column name where smiles are given in csv-file. Default is "smiles".
            add_hydrogen (bool): Whether to add H after smile translation. Default is True.
            sanitize (bool): Whether to sanitize molecule.
            make_conformers (bool): Whether to make conformers. Default is True.
            optimize_conformer (bool): Whether to optimize conformer via force field.
                Only possible with :obj:`make_conformers`. Default is True.
            external_program (dict): External program for translating smiles. Default is None.
                If you want to use an external program you have to supply a dictionary of the form:
                {"class_name": "balloon", "config": {"balloon_executable_path": ..., ...}}.
                Note that usually the parameters like :obj:`add_hydrogen` are ignored. And you need to control the
                SDF file generation within `config` of the :obj:`external_program`.
            num_workers (int): Parallel execution for translating smiles.

        Returns:
            self
        """
        if os.path.exists(self.file_path_mol) and not overwrite:
            self.info("Found SDF %s of pre-computed structures." % self.file_path_mol)
            return self

        self.read_in_table_file()
        smiles = self.data_frame[smiles_column_name].values

        mb = self._smiles_to_mol_list(smiles,
                                      add_hydrogen=add_hydrogen, sanitize=sanitize,
                                      make_conformers=make_conformers, optimize_conformer=optimize_conformer,
                                      external_program=external_program, num_workers=num_workers)

        write_mol_block_list_to_sdf(mb, self.file_path_mol)
        return self

    def read_in_memory(self,  label_column_name: str = None, has_conformers: bool = True,
                       add_hydrogen: bool = True):
        r"""Load list of molecules from cached SDF-file in into memory. File name must be given in :obj:`file_name` and
        path information in the constructor of this class. Extract basic graph information from mol-blocks.
        No further attributes are computed as default. Use :obj:`set_attributes` for this purpose.
        It further checks the csv-file for graph labels specified by :obj:`label_column_name`.
        Labels that do not have valid smiles or molecule in the SDF-file are also skipped.
        The assignment to original IDs is stored in :obj:`valid_molecule_id`.

        Args:
            label_column_name (str): Column name in the csv-file where to take graph labels from.
            add_hydrogen (bool): Whether to keep hydrogen after reading the mol-information. Default is True.
            has_conformers (bool): If molecules has 3D coordinates pre-computed.
                For multi-targets you can supply a list of column names or positions. Also a slice can be provided
                for selecting columns as graph labels. Default is None.

        Returns:
            self
        """
        # Read the data from a csv-file.
        data = pd.read_csv(os.path.join(self.data_directory, self.file_name))

        # Find columns to take graph labels from.
        self.data_keys = data.columns
        graph_labels_all = pandas_data_frame_columns_to_numpy(data, label_column_name)

        if not os.path.exists(self.file_path_mol):
            raise FileNotFoundError("Can not load molecules for dataset %s" % self.dataset_name)

        self.info("Read mol-blocks from %s of pre-computed structures..." % self.file_path_mol)
        mols = read_mol_list_from_sdf_file(self.file_path_mol)

        # Main loop to read molecules from mol-block
        node_symbol = []
        node_coordinates = []
        node_number = []
        edge_indices = []
        edge_number = []
        num_mols = len(mols)
        graph_labels = []
        counter_iter = 0
        for i, x in enumerate(mols):
            mg = MolecularGraphRDKit(add_hydrogen=add_hydrogen).from_mol_block(x, sanitize=True)
            if mg.mol is None:
                edge_indices.append(None)
                edge_number.append(None)
                node_symbol.append(None)
                node_number.append(None)
                graph_labels.append(None)
                node_coordinates.append(None)
                continue
            # Append all valid tensor quantities
            temp_edge = mg.edge_number
            edge_indices.append(temp_edge[0])
            edge_number.append(np.array(temp_edge[1], dtype="int"))
            node_symbol.append(mg.node_symbol)
            node_number.append(mg.node_number)
            graph_labels.append(graph_labels_all[i])
            node_coordinates.append(mg.node_coordinates)
            counter_iter += 1
            if i % 1000 == 0:
                self.info(" ... read molecules {0} from {1}".format(i, num_mols))

        self.assign_property("node_symbol", node_symbol)
        self.assign_property("node_coordinates",  node_coordinates)
        self.assign_property("node_number", node_number)
        self.assign_property("graph_size", [None if x is None else len(x) for x in node_number])
        self.assign_property("edge_indices", edge_indices)
        self.assign_property("graph_labels", graph_labels)
        self.assign_property("edge_number", edge_number)
        return self

    def set_attributes(self,
                       nodes: list = None,
                       edges: list = None,
                       graph: list = None,
                       encoder_nodes: dict = None,
                       encoder_edges: dict = None,
                       encoder_graph: dict = None,
                       add_hydrogen: bool = False,
                       has_conformers: bool = True,
                       ):
        r"""Set further molecular attributes or features by string identifier. Requires :obj:`MolecularGraphRDKit`.
        Reset edges and nodes with new attributes and edge indices. Default values are features that has been used
        by `Luo et al (2019) <https://doi.org/10.1021/acs.jmedchem.9b00959>`_.

        Args:
            nodes (list): A list of node attributes
            edges (list): A list of edge attributes
            graph (list): A list of graph attributes.
            encoder_nodes (dict): A dictionary of callable encoder where the key matches the attribute.
            encoder_edges (dict): A dictionary of callable encoder where the key matches the attribute.
            encoder_graph (dict): A dictionary of callable encoder where the key matches the attribute.
            add_hydrogen (bool): Whether to remove hydrogen.
            has_conformers (bool): If molecules needs 3D coordinates pre-computed.

        Returns:
            self
        """
        if not os.path.exists(self.file_path_mol):
            raise FileNotFoundError("Can not load molecules for dataset %s" % self.dataset_name)

        self.info("Making attributes...")

        mols = read_mol_list_from_sdf_file(self.file_path_mol)

        # Choose default values here:
        if nodes is None:
            nodes = ['Symbol', 'TotalDegree', 'FormalCharge', 'NumRadicalElectrons', 'Hybridization',
                     'IsAromatic', 'IsInRing', 'TotalNumHs', 'CIPCode', "ChiralityPossible", "ChiralTag"]
        if edges is None:
            edges = ['BondType', 'IsAromatic', 'IsConjugated', 'IsInRing', "Stereo"]
        if graph is None:
            graph = ['ExactMolWt', 'NumAtoms']
        if encoder_nodes is None:
            encoder_nodes = {
                "Symbol": OneHotEncoder(
                    ['B', 'C', 'N', 'O', 'F', 'Si', 'P', 'S', 'Cl', 'As', 'Se', 'Br', 'Te', 'I', 'At'], dtype="str"),
                "Hybridization": OneHotEncoder([2, 3, 4, 5, 6]),
                "TotalDegree": OneHotEncoder([0, 1, 2, 3, 4, 5], add_unknown=False),
                "TotalNumHs": OneHotEncoder([0, 1, 2, 3, 4], add_unknown=False),
                "CIPCode": OneHotEncoder(['R', 'S'], add_unknown=False, dtype="str")
            }
        if encoder_edges is None:
            encoder_edges = {
                "BondType": OneHotEncoder([1, 2, 3, 12], add_unknown=False),
                "Stereo": OneHotEncoder([0, 1, 2, 3], add_unknown=False),
            }
        if encoder_graph is None:
            encoder_graph = {}

        for key, value in encoder_nodes.items():
            encoder_nodes[key] = self._deserialize_encoder(value)
        for key, value in encoder_edges.items():
            encoder_edges[key] = self._deserialize_encoder(value)
        for key, value in encoder_graph.items():
            encoder_graph[key] = self._deserialize_encoder(value)

        # Reset all attributes
        graph_attributes = []
        node_attributes = []
        edge_attributes = []
        edge_number = []
        edge_indices = []
        node_coordinates = []
        node_symbol = []
        node_number = []
        num_mols = len(mols)
        counter_iter = 0
        for i, sm in enumerate(mols):
            mg = MolecularGraphRDKit(add_hydrogen=add_hydrogen).from_mol_block(sm, sanitize=True)
            if mg.mol is None:
                node_coordinates.append(None)
                edge_indices.append(None)
                edge_number.append(None)
                node_attributes.append(None)
                edge_attributes.append(None)
                graph_attributes.append(None)
                node_symbol.append(None)
                node_number.append(None)
                continue
            # Append all valid tensor properties
            temp_edge = mg.edge_number
            node_coordinates.append(np.array(mg.node_coordinates, dtype="float32"))
            edge_indices.append(np.array(temp_edge[0], dtype="int64"))
            edge_number.append(np.array(temp_edge[1], dtype="int"))
            node_attributes.append(np.array(mg.node_attributes(nodes, encoder_nodes), dtype="float32"))
            edge_attributes.append(np.array(mg.edge_attributes(edges, encoder_edges)[1], dtype="float32"))
            graph_attributes.append(np.array(mg.graph_attributes(graph, encoder_graph), dtype="float32"))
            node_symbol.append(mg.node_symbol)
            node_number.append(mg.node_number)
            counter_iter += 1
            if i % 1000 == 0:
                self.info(" ... read molecules {0} from {1}".format(i, num_mols))

        self.assign_property("graph_size", [None if x is None else len(x) for x in node_number])
        self.assign_property("graph_attributes", graph_attributes)
        self.assign_property("node_attributes", node_attributes)
        self.assign_property("edge_attributes", edge_attributes)
        self.assign_property("edge_indices", edge_indices)
        self.assign_property("node_coordinates", node_coordinates)
        self.assign_property("node_symbol", node_symbol)
        self.assign_property("node_number", node_number)

        if self.logger.getEffectiveLevel() < 20:
            for key, value in encoder_nodes.items():
                if hasattr(value, "report"):
                    value.report(name=key)
            for key, value in encoder_edges.items():
                if hasattr(value, "report"):
                    value.report(name=key)
            for key, value in encoder_graph.items():
                if hasattr(value, "report"):
                    value.report(name=key)

        return self

    @staticmethod
    def _deserialize_encoder(encoder_identifier):
        """Serialization. Will maybe include keras in the future.

        Args:
            encoder_identifier: Identifier, class or function of an encoder.

        Returns:
            obj: Deserialized encoder.
        """
        if isinstance(encoder_identifier, dict):
            if encoder_identifier["class_name"] == "OneHotEncoder":
                return OneHotEncoder.from_config(encoder_identifier["config"])
        elif hasattr(encoder_identifier, "__call__"):
            return encoder_identifier
        else:
            raise ValueError("Unable to deserialize encoder %s " % encoder_identifier)

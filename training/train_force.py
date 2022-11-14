import numpy as np
import matplotlib as mpl
# mpl.use('Agg')
import time
import os
import argparse
from datetime import timedelta
from tensorflow_addons import optimizers, metrics
import kgcnn.training.schedule
import kgcnn.training.scheduler
from kgcnn.training.history import save_history_score
from sklearn.model_selection import KFold
from kgcnn.utils.plots import plot_train_test_loss, plot_predict_true
from kgcnn.model.utils import get_model_class
from kgcnn.data.serial import deserialize as deserialize_dataset
from kgcnn.hyper.hyper import HyperParameter
from kgcnn.utils.devices import set_devices_gpu
from kgcnn.scaler.force import EnergyForceExtensiveScaler
from kgcnn.metrics.loss import RaggedMeanAbsoluteError

# Input arguments from command line.
parser = argparse.ArgumentParser(description='Train a GNN on an Energy-Force Dataset.')
parser.add_argument("--model", required=False, help="Graph model to train.", default="Schnet")
parser.add_argument("--dataset", required=False, help="Name of the dataset or leave empty for custom dataset.",
                    default="MD17Dataset")
parser.add_argument("--hyper", required=False, help="Filepath to hyper-parameter config file (.py or .json).",
                    default="hyper/hyper_md17.py")
parser.add_argument("--make", required=False, help="Name of the make function or class for model.",
                    default="make_force_model")
parser.add_argument("--gpu", required=False, help="GPU index used for training.",
                    default=None, nargs="+", type=int)
parser.add_argument("--fold", required=False, help="Split or fold indices to run.",
                    default=None, nargs="+", type=int)
args = vars(parser.parse_args())
print("Input of argparse:", args)

# Main parameter about model, dataset, and hyper-parameter
model_name = args["model"]
dataset_name = args["dataset"]
hyper_path = args["hyper"]
make_function = args["make"]
gpu_to_use = args["gpu"]
execute_folds = args["fold"]

# Assigning GPU.
set_devices_gpu(gpu_to_use)

# HyperParameter is used to store and verify hyperparameter.
hyper = HyperParameter(hyper_path, model_name=model_name, model_class=make_function, dataset_name=dataset_name)

# Model Selection to load a model definition from a module in kgcnn.literature
try:
    make_model = get_model_class(model_name, make_function)
except ModuleNotFoundError:
    make_model = get_model_class(hyper["model"]["module_name"], hyper["model"]["class_name"])

# Loading a specific per-defined dataset from a module in kgcnn.data.datasets.
# However, the construction must be fully defined in the data section of the hyperparameter,
# including all methods to run on the dataset. Information required in hyperparameter are for example 'file_path',
# 'data_directory' etc.
# Making a custom training script rather than configuring the dataset via hyperparameter can be
# more convenient.
dataset = deserialize_dataset(hyper["data"]["dataset"])

# Check if dataset has the required properties for model input. This includes a quick shape comparison.
# The name of the keras `Input` layer of the model is directly connected to property of the dataset.
# Example 'edge_indices' or 'node_attributes'. This couples the keras model to the dataset.
dataset.assert_valid_model_input(hyper["model"]["config"]["inputs"])

# Filter the dataset for invalid graphs. At the moment invalid graphs are graphs which do not have the property set,
# which is required by the model's input layers, or if a tensor-like property has zero length.
dataset.clean(hyper["model"]["config"]["inputs"])
data_length = len(dataset)  # Length of the cleaned dataset.

# For a ForceDataset, train on energy and force output.
# The name of force and energy graph property must be provided in hyperparameter.
energy_output, force_output = hyper["model"]["config"]["outputs"]
energy = np.array(dataset.get(energy_output["name"]))
force = dataset.get(force_output["name"])
label_names = dataset.label_names if hasattr(dataset, "label_names") else ""
label_units = dataset.label_units if hasattr(dataset, "label_units") else ""
if len(energy.shape) <= 1:
    energy = np.expand_dims(energy, axis=-1)

# Training on multiple targets for regression. This can is often required to train on orbital energies of ground
# or excited state or energies and enthalpies etc.
multi_target_indices = hyper["training"]["multi_target_indices"]
print("Energy '%s' in '%s' has shape '%s'." % (label_names, label_units, energy.shape))

# For ForceDataset, also the atomic number is required to properly pre-scale extensive quantities like total energy.
atoms = dataset.get("node_number")
coord = dataset.get("node_coordinates")

# Cross-validation via random KFold split form `sklearn.model_selection`.
# Or from dataset information.
if hyper["training"]["cross_validation"] is None:
    print("Using dataset splits.")
    train_test_indices = dataset.get_split_indices()
else:
    kf = KFold(**hyper["training"]["cross_validation"]["config"])
    train_test_indices = [
        [train_index, test_index] for train_index, test_index in kf.split(X=np.zeros((data_length, 1)), y=energy)]

# Training on splits. Since training on Force datasets can be expensive, there is a 'execute_splits' parameter to not
# train on all splits for testing. Can be set via command line or hyperparameter.
if "execute_folds" in hyper["training"]:
    execute_folds = hyper["training"]["execute_folds"]
splits_done = 0
history_list, test_indices_list = [], []
model, hist, x_test, y_test, scaler, atoms_test, coord_test = None, None, None, None, None, None, None

for i, (train_index, test_index) in enumerate(train_test_indices):

    # Only do execute_splits out of the k-folds of cross-validation.
    if execute_folds:
        if i not in execute_folds:
            continue
    print("Running training on fold: %s" % i)

    # Make the model for current split using model kwargs from hyperparameter.
    # They are always updated on top of the models default kwargs.
    model = make_model(**hyper["model"]["config"])

    # First select training and test graphs from indices, then convert them into tensorflow tensor
    # representation. Which property of the dataset and whether the tensor will be ragged is retrieved from the
    # kwargs of the keras `Input` layers ('name' and 'ragged').
    x_train = dataset[train_index].tensor(hyper["model"]["config"]["inputs"])
    x_test = dataset[test_index].tensor(hyper["model"]["config"]["inputs"])
    # Energies
    energy_train = energy[train_index]
    energy_test = energy[test_index]
    # Coordinates as list.
    coord_train = [coord[i] for i in train_index]
    coord_test = [coord[i] for i in test_index]
    # Also keep the same information for atomic numbers of the molecules.
    atoms_train = [atoms[i] for i in train_index]
    atoms_test = [atoms[i] for i in test_index]
    # Force information. Forces will be a ragged tensor too.
    force_train = [force[i] for i in train_index]
    force_test = [force[i] for i in test_index]

    # Normalize training and test targets. For Force datasets this training script uses the
    # `EnergyForceExtensiveScaler` class.
    if "scaler" in hyper["training"]:
        print("Using `EnergyForceExtensiveScaler`.")
        # Atomic number force and energy argument here!
        # Note that `EnergyForceExtensiveScaler` does not use X argument at the moment.
        scaler = EnergyForceExtensiveScaler(**hyper["training"]["scaler"]["config"]).fit(
            X=coord_train, y=energy_train, atomic_number=atoms_train, force=force_train)
        _, energy_train, force_train = scaler.transform(
            X=coord_train, y=energy_train, atomic_number=atoms_train, force=force_train)
        _, energy_test, force_test = scaler.transform(
            X=coord_test, y=energy_test, atomic_number=atoms_test, force=force_test)

        # If scaler was used we add rescaled standard metrics to compile.
        scaler_scale = scaler.get_scaling()
        if scaler.scale_ is not None:
            pass
        metrics = []
    else:
        print("Not using QMGraphLabelScaler.")
        metrics = None

    # Compile model with optimizer and loss
    model.compile(**hyper.compile(loss=["mean_absolute_error", RaggedMeanAbsoluteError()], metrics=metrics))
    print(model.summary())

    # Start and time training
    start = time.process_time()
    hist = model.fit(x_train, [energy_train, force_train],
                     validation_data=(x_test, [energy_test, force_test]),
                     **hyper.fit())
    stop = time.process_time()
    print("Print Time for training: ", str(timedelta(seconds=stop - start)))

    # Get loss from history
    history_list.append(hist)
    test_indices_list.append([train_index, test_index])
    splits_done = splits_done + 1

# Make output directory
filepath = hyper.results_file_path()
postfix_file = hyper["info"]["postfix_file"]

# Plot training- and test-loss vs epochs for all splits.
data_unit = hyper["data"]["data_unit"]
plot_train_test_loss(history_list, loss_name=None, val_loss_name=None,
                     model_name=model_name, data_unit=data_unit, dataset_name=dataset_name,
                     filepath=filepath, file_name=f"loss{postfix_file}.png")

# Plot prediction
predicted_y = model.predict(x_test, verbose=0)
true_y = y_test

if scaler:
    _, rescaled_predicted_energy, rescaled_predicted_force = scaler.inverse_transform(
        X=coord_test, y=predicted_y[0], force=predicted_y[1], atomic_number=atoms_test)
    predicted_y = [rescaled_predicted_energy, rescaled_predicted_force]
    _, true_energy, true_force = scaler.inverse_transform(
        X=coord_test, y=predicted_y[0], force=predicted_y[1], atomic_number=atoms_test)
    true_y = [true_energy, true_force]

plot_predict_true(predicted_y[0], true_y[0],
                  filepath=filepath, data_unit=label_units,
                  model_name=model_name, dataset_name=dataset_name, target_names=label_names,
                  file_name=f"predict_energy{postfix_file}.png")

plot_predict_true(predicted_y[1], true_y[1],
                  filepath=filepath, data_unit=label_units,
                  model_name=model_name, dataset_name=dataset_name, target_names=label_names,
                  file_name=f"predict_force{postfix_file}.png")

# Save keras-model to output-folder.
model.save(os.path.join(filepath, f"model{postfix_file}"))

# Save original data indices of the splits.
np.savez(os.path.join(filepath, f"{model_name}_kfold_splits{postfix_file}.npz"), test_indices_list)

# Save hyperparameter again, which were used for this fit.
hyper.save(os.path.join(filepath, f"{model_name}_hyper{postfix_file}.json"))

# Save score of fit result for as text file.
save_history_score(history_list, loss_name=None, val_loss_name=None,
                   model_name=model_name, data_unit=data_unit, dataset_name=dataset_name,
                   model_class=make_function, multi_target_indices=multi_target_indices, execute_folds=execute_folds,
                   filepath=filepath, file_name=f"score{postfix_file}.yaml")

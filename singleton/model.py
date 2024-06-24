import torch
import numpy as np

import torch
import torch.nn as nn
import numpy as np
import os

model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../model.pth")


# Define the same neural network architecture used for training
class SimpleNN(nn.Module):
    def __init__(self, input_features):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(input_features, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 2)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def initModel():
    # Initialize the model with the correct number of input features
    # Adjust the number of features if your model differs
    model = SimpleNN(input_features=6)

    # Load the saved model weights
    model.load_state_dict(torch.load(model_path))
    model.eval()
    return model


def predict(model, age, sex, testA, testB, testC, average_result):
    # Prepare the input data (convert sex to numerical, etc.)
    # Adjust preprocessing as per your training data requirements
    sex = 0 if sex == "M" else 1  # Example preprocessing step
    input_features = np.array([[age, sex, testA, testB, testC, average_result]])

    # Convert to PyTorch tensor
    input_tensor = torch.tensor(input_features, dtype=torch.float32)

    # Make the prediction
    with torch.no_grad():
        output = model(input_tensor)
        _, predicted = torch.max(output, 1)

    return predicted.item()

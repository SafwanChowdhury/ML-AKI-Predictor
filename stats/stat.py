import pandas as pd


# Load the CSV file for ground truth
ground_truth = pd.read_csv("aki.csv")

# Read the log file and filter page logs
with open("../logs.log", "r") as file:
    page_logs = []
    for line in file:
        if "PAGE:" in line:
            parts = line.strip().split("PAGE:")[1].split(":")
            mrn, date = parts[0], ":".join(parts[1:])
            page_logs.append({"mrn": mrn.strip(), "date": date.strip()})

# Convert page logs to DataFrame
predictions = pd.DataFrame(page_logs)

# Create unique identifiers by combining MRN and date for both DataFrames
ground_truth["identifier"] = (
    ground_truth["mrn"].astype(str) + "-" + ground_truth["date"]
)
predictions["identifier"] = predictions["mrn"].astype(str) + "-" + predictions["date"]

print(ground_truth.head())
print(predictions.head())

# Extract unique identifiers
ground_truth_identifiers = set(ground_truth["identifier"])
predictions_identifiers = set(predictions["identifier"])

# Calculate statistics
true_positives = ground_truth_identifiers.intersection(predictions_identifiers)
false_negatives = ground_truth_identifiers.difference(predictions_identifiers)
false_positives = predictions_identifiers.difference(ground_truth_identifiers)

# Calculate precision, recall, and F1 score
precision = (
    len(true_positives) / (len(true_positives) + len(false_positives))
    if (len(true_positives) + len(false_positives)) > 0
    else 0
)
recall = (
    len(true_positives) / (len(true_positives) + len(false_negatives))
    if (len(true_positives) + len(false_negatives)) > 0
    else 0
)
f1_score = (
    2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
)

f3_score = (
    3 * (precision * recall) / (2 * precision + recall)
    if (precision + recall) > 0
    else 0
)

print(f"True Positives: {len(true_positives)}")
print(f"False Negatives (Misses): {len(false_negatives)}")
print(f"False Positives: {len(false_positives)}")
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
print(f"F1 Score: {f1_score:.2f}")
print(f"F3 Score: {f3_score:.2f}")

from prometheus_client import Counter, Gauge, Histogram, Summary

# Existing Metric
messages = Counter("messages_received", "Number of messages received")

# Additional Metrics
blood_tests_received = Counter(
    "blood_tests_received", "Number of blood test results received"
)

patient_admitted = Counter("patient_admitted", "Number of patients admitted")

aki_positive_predictions = Counter(
    "aki_positive_predictions", "Number of positive AKI model predictions"
)
pager_http_failures = Counter(
    "pager_http_failures", "Number of failed pager HTTP requests (non-200 status)"
)
mllp_reconnections = Counter(
    "mllp_reconnections", "Number of reconnections to the MLLP socket"
)
blood_test_result_values = Histogram(
    "blood_test_result_values",
    "Distribution of blood test result values",
    buckets=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, float("inf")],
)

request_time = Summary("request_processing_seconds", "Time spent processing request")

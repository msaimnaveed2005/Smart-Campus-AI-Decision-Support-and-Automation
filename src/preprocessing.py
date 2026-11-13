"""
Input & Preprocessing Module
=============================
Handles the first stage of the pipeline:
- Validates incoming structured requests (checks required fields, value ranges)
- Normalizes values (severity to 0-1 range)
- Builds the 7-element ANN feature vector
- Derives computed fields (crowd level, distance)

If validation fails, the pipeline halts with clear error messages.
This module also prepares the standard request object used by all downstream modules.
"""

import math
from campus_data import CAMPUS_NODES, VALID_REQUEST_TYPES, VALID_ROLES


class PreprocessingResult:
    """
    Container for preprocessing output.
    Stores the validated/normalized request, feature vector, and any errors.
    """

    def __init__(self, valid, request=None, feature_vector=None, errors=None, exec_time=0):
        self.valid = valid                    # Whether the request passed validation
        self.request = request                # The normalized request dict
        self.feature_vector = feature_vector  # 7-element list [x1..x7] for ANN
        self.errors = errors or []            # List of validation error messages
        self.exec_time = exec_time            # Processing time in ms

    def __str__(self):
        if self.valid:
            return (f"Preprocessing: VALID\n"
                    f"  Feature vector: {self.feature_vector}\n"
                    f"  Fields validated: {len(self.request)}")
        else:
            return f"Preprocessing: INVALID\n  Errors: {', '.join(self.errors)}"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = {
            "valid": self.valid,
            "exec_time_ms": round(self.exec_time, 2),
        }
        if self.valid:
            result["request"] = self.request
            result["feature_vector"] = self.feature_vector
            result["fields_validated"] = len(self.request) if self.request else 0
        else:
            result["errors"] = self.errors
        return result


# ─── ROLE AND REQUEST TYPE ENCODING ────────────────────────────────────

ROLE_ENCODING = {"Student": 0.0, "Instructor": 0.5, "Staff": 1.0}

REQUEST_TYPE_ENCODING = {
    "Navigation_Only": 0.0,
    "Eligibility_Check": 0.25,
    "Booking_or_Scheduling": 0.5,
    "Urgent_Service_Request": 0.75,
    "Full_Service_Request": 1.0,
}


def validate_request(request):
    """
    Validate a structured request dictionary.
    Checks for required fields, valid values, and correct types.

    Args:
        request: Dictionary with user request data.
            Required keys: user (dict with name, roll, role),
                           request_type, severity, destination

    Returns:
        Tuple of (is_valid: bool, errors: list of error strings)
    """
    errors = []

    # Check top-level required fields
    if not isinstance(request, dict):
        return False, ["Request must be a dictionary"]

    # User validation
    user = request.get("user")
    if not user or not isinstance(user, dict):
        errors.append("Missing or invalid 'user' field (must include name, roll, role)")
    else:
        if not user.get("name"):
            errors.append("User name is required")
        if not user.get("roll"):
            errors.append("User roll number is required")
        role = user.get("role")
        if role not in VALID_ROLES:
            errors.append(f"Invalid role '{role}'. Must be one of: {', '.join(VALID_ROLES)}")

    # Request type validation
    req_type = request.get("request_type")
    if req_type not in VALID_REQUEST_TYPES:
        errors.append(f"Invalid request_type '{req_type}'. Must be one of: {', '.join(VALID_REQUEST_TYPES)}")

    # Severity validation
    severity = request.get("severity")
    if severity is None:
        errors.append("Severity is required")
    elif not isinstance(severity, (int, float)):
        errors.append("Severity must be a number")
    elif severity < 0.0 or severity > 10.0:
        errors.append("Severity must be between 0.0 and 10.0")

    # Destination validation
    destination = request.get("destination")
    if not destination:
        errors.append("Destination is required")
    elif destination not in CAMPUS_NODES:
        errors.append(f"Invalid destination '{destination}'. Must be a valid campus node")

    # Origin validation (required for Navigation and Full Service)
    origin = request.get("origin")
    if req_type in ["Navigation_Only", "Full_Service_Request", "Urgent_Service_Request"]:
        if not origin:
            errors.append(f"Origin is required for {req_type}")
        elif origin not in CAMPUS_NODES:
            errors.append(f"Invalid origin '{origin}'. Must be a valid campus node")

    # Time sensitivity validation (optional, defaults to 0.5)
    time_sensitivity = request.get("time_sensitivity", 0.5)
    if not isinstance(time_sensitivity, (int, float)):
        errors.append("Time sensitivity must be a number")
    elif time_sensitivity < 0.0 or time_sensitivity > 1.0:
        errors.append("Time sensitivity must be between 0.0 and 1.0")

    return len(errors) == 0, errors


def compute_distance(origin, destination):
    """
    Compute normalized Euclidean distance between two campus nodes.
    Normalizes to 0-1 range based on max possible distance across the campus.

    Args:
        origin: Name of the origin node
        destination: Name of the destination node

    Returns:
        Normalized distance (0.0 to 1.0)
    """
    if not origin or origin not in CAMPUS_NODES or destination not in CAMPUS_NODES:
        return 0.0

    a = CAMPUS_NODES[origin]
    b = CAMPUS_NODES[destination]
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    raw = math.sqrt(dx * dx + dy * dy)

    # Max possible distance across campus (Bus_Stop(0,1) to Seminar_Room(10,4))
    max_dist = math.sqrt(10**2 + 5**2)  # ~11.18
    return round(min(raw / max_dist, 1.0), 2)


def compute_crowd_level(hour=11):
    """
    Compute a simulated crowd level based on time of day.
    In a real system this would come from sensors or historical data.

    Args:
        hour: Hour of day (0-23). Default 11 (late morning, moderate crowd).

    Returns:
        Crowd level (0.0 to 1.0)
    """
    # Simple model: peak at noon, low at night
    if 9 <= hour <= 14:
        return round(0.3 + 0.1 * abs(hour - 11.5) / 2.5, 2)
    elif 15 <= hour <= 18:
        return 0.25
    else:
        return 0.10


def preprocess_request(request):
    """
    Full preprocessing pipeline: validate, normalize, build feature vector.
    This is the main function called by the router.

    Args:
        request: Raw structured request dictionary

    Returns:
        PreprocessingResult with validated request and feature vector
    """
    import time as _time
    start = _time.perf_counter()

    # Step 1: Validate
    is_valid, errors = validate_request(request)
    if not is_valid:
        exec_time = (_time.perf_counter() - start) * 1000
        return PreprocessingResult(valid=False, errors=errors, exec_time=exec_time)

    # Step 2: Normalize and derive values
    severity = request["severity"]
    normalized_severity = round(severity / 10.0, 2)

    time_sensitivity = request.get("time_sensitivity", 0.5)
    origin = request.get("origin")
    destination = request["destination"]

    crowd_level = request.get("crowd_level", compute_crowd_level())
    distance = request.get("distance", compute_distance(origin, destination))

    # Eligibility flag: declared by user or pre-checked
    # In real system this would look up academic records
    eligibility = request.get("eligibility_flag", 1.0)

    # Step 3: Build feature vector [x1..x7]
    role = request["user"]["role"]
    req_type = request["request_type"]

    feature_vector = [
        ROLE_ENCODING.get(role, 0.0),           # x1: Role
        REQUEST_TYPE_ENCODING.get(req_type, 0.0), # x2: RequestType
        normalized_severity,                      # x3: Severity (normalized)
        round(time_sensitivity, 2),               # x4: TimeSensitivity
        round(crowd_level, 2),                    # x5: CrowdLevel (derived)
        round(distance, 2),                       # x6: Distance (derived)
        round(eligibility, 2),                    # x7: Eligibility flag
    ]

    # Step 4: Build normalized request object
    normalized_request = {
        "user": request["user"],
        "request_type": req_type,
        "severity": severity,
        "severity_normalized": normalized_severity,
        "time_sensitivity": time_sensitivity,
        "crowd_level": crowd_level,
        "distance": distance,
        "eligibility_flag": eligibility,
        "origin": origin,
        "destination": destination,
        "feature_vector": feature_vector,
    }

    exec_time = (_time.perf_counter() - start) * 1000

    return PreprocessingResult(
        valid=True,
        request=normalized_request,
        feature_vector=feature_vector,
        exec_time=exec_time,
    )


# ─── TESTING ───────────────────────────────────────────────────────────

def test_preprocessing():
    """Test the preprocessing module with valid and invalid requests."""
    print("=" * 60)
    print("INPUT & PREPROCESSING MODULE — TEST SUITE")
    print("=" * 60)

    # Test 1: Valid request (Ali, Full Service)
    print("\n--- Test 1: Valid request (Ali, Full Service) ---")
    request_ali = {
        "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
        "request_type": "Full_Service_Request",
        "severity": 8.5,
        "time_sensitivity": 0.92,
        "crowd_level": 0.40,
        "distance": 0.32,
        "eligibility_flag": 1.0,
        "origin": "Main_Gate",
        "destination": "AI_Lab",
    }
    result = preprocess_request(request_ali)
    print(result)
    print(f"Feature vector: {result.feature_vector}")
    assert result.valid, "Ali's request should be valid"
    assert result.feature_vector[2] == 0.85, f"Normalized severity should be 0.85, got {result.feature_vector[2]}"
    print("✓ PASSED\n")

    # Test 2: Invalid severity (Scenario 5)
    print("--- Test 2: Invalid severity ---")
    request_bad = {
        "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
        "request_type": "Full_Service_Request",
        "severity": -1,
        "time_sensitivity": 0.5,
        "origin": "Main_Gate",
        "destination": "AI_Lab",
    }
    result2 = preprocess_request(request_bad)
    print(result2)
    assert not result2.valid, "Should be invalid"
    assert "Severity must be between 0.0 and 10.0" in result2.errors[0]
    print("✓ PASSED\n")

    # Test 3: Missing fields
    print("--- Test 3: Missing destination ---")
    result3 = preprocess_request({"user": {"name": "Ali", "roll": "24F-1234", "role": "Student"}, "request_type": "Navigation_Only", "severity": 5})
    print(result3)
    assert not result3.valid
    print("✓ PASSED\n")

    # Test 4: Invalid role
    print("--- Test 4: Invalid role ---")
    result4 = preprocess_request({
        "user": {"name": "Ali", "roll": "24F-1234", "role": "Admin"},
        "request_type": "Navigation_Only", "severity": 5,
        "origin": "Main_Gate", "destination": "AI_Lab",
    })
    print(result4)
    assert not result4.valid
    print("✓ PASSED\n")

    # Test 5: Distance computation
    print("--- Test 5: Distance computation ---")
    d = compute_distance("Main_Gate", "AI_Lab")
    print(f"Main_Gate → AI_Lab distance: {d}")
    assert 0 < d < 1, "Distance should be normalized between 0 and 1"
    print("✓ PASSED")

    print("\n" + "=" * 60)
    print("ALL PREPROCESSING TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_preprocessing()


"""
Mock data for testing the EOL Tester system
"""

from datetime import datetime, timedelta

# Mock database records for testing
MOCK_DATABASE_RECORDS = [
    {
        "LOT_NUMBER": "2412010010001",
        "PART_NUMBER": "ALC001",
        "EMP_CODE": "EMP001",
        "TEST_DATE": "2024-12-01",
        "TEST_TIME": "10:00:00",
        "L1_VALUE": 12.5,
        "L2_VALUE": 10.2,
        "L3_VALUE": 15.1,
        "L4_VALUE": 12.0,
        "P1_VALUE": 6.8,
        "P2_VALUE": 5.6,
        "P3_VALUE": 7.9,
        "P4_VALUE": 4.7,
        "OVERALL_RESULT": "PASS",
        "FAILED_DEVICES": "",
        "TEST_DURATION": 45.5,
        "CREATED_AT": "2024-12-01 10:00:00"
    },
    {
        "LOT_NUMBER": "2412010010002",
        "PART_NUMBER": "ALC002", 
        "EMP_CODE": "EMP002",
        "TEST_DATE": "2024-12-01",
        "TEST_TIME": "11:00:00",
        "L1_VALUE": 11.8,
        "L2_VALUE": 9.9,
        "L3_VALUE": 14.2,
        "L4_VALUE": 11.5,
        "P1_VALUE": 6.2,
        "P2_VALUE": 5.1,
        "P3_VALUE": 7.3,
        "P4_VALUE": 4.2,
        "OVERALL_RESULT": "PASS",
        "FAILED_DEVICES": "",
        "TEST_DURATION": 42.3,
        "CREATED_AT": "2024-12-01 11:00:00"
    },
    {
        "LOT_NUMBER": "2412010010003",
        "PART_NUMBER": "ALC001",
        "EMP_CODE": "EMP001",
        "TEST_DATE": "2024-12-01",
        "TEST_TIME": "12:00:00",
        "L1_VALUE": 13.2,
        "L2_VALUE": 10.8,
        "L3_VALUE": 15.8,
        "L4_VALUE": 12.9,
        "P1_VALUE": 7.1,
        "P2_VALUE": 5.9,
        "P3_VALUE": 8.2,
        "P4_VALUE": 5.0,
        "OVERALL_RESULT": "FAIL",
        "FAILED_DEVICES": "L3,P3",
        "TEST_DURATION": 38.7,
        "CREATED_AT": "2024-12-01 12:00:00"
    }
]

# Mock part specifications for testing
MOCK_PART_SPECIFICATIONS = {
    "ALC001": {
        "PART_NAME": "Automotive Lighting Component 001",
        "specifications": {
            "L1_MIN": 10.0,
            "L1_MAX": 15.0,
            "L2_MIN": 8.0,
            "L2_MAX": 12.0,
            "L3_MIN": 12.0,
            "L3_MAX": 16.0,
            "L4_MIN": 10.0,
            "L4_MAX": 14.0,
            "P1_MIN": 5.0,
            "P1_MAX": 8.0,
            "P2_MIN": 4.0,
            "P2_MAX": 7.0,
            "P3_MIN": 6.0,
            "P3_MAX": 9.0,
            "P4_MIN": 3.0,
            "P4_MAX": 6.0
        },
        "IMAGE_PATH": "images/alc001.jpg",
        "LABEL_COORDINATES": {
            "L1": {"x": 100, "y": 150},
            "L2": {"x": 200, "y": 150},
            "L3": {"x": 300, "y": 150},
            "L4": {"x": 400, "y": 150},
            "P1": {"x": 100, "y": 250},
            "P2": {"x": 200, "y": 250},
            "P3": {"x": 300, "y": 250},
            "P4": {"x": 400, "y": 250}
        }
    },
    "ALC002": {
        "PART_NAME": "Automotive Lighting Component 002",
        "specifications": {
            "L1_MIN": 9.0,
            "L1_MAX": 13.0,
            "L2_MIN": 7.0,
            "L2_MAX": 11.0,
            "L3_MIN": 11.0,
            "L3_MAX": 15.0,
            "L4_MIN": 9.0,
            "L4_MAX": 13.0,
            "P1_MIN": 4.5,
            "P1_MAX": 7.5,
            "P2_MIN": 3.5,
            "P2_MAX": 6.5,
            "P3_MIN": 5.5,
            "P3_MAX": 8.5,
            "P4_MIN": 2.5,
            "P4_MAX": 5.5
        },
        "IMAGE_PATH": "images/alc002.jpg",
        "LABEL_COORDINATES": {
            "L1": {"x": 120, "y": 160},
            "L2": {"x": 220, "y": 160},
            "L3": {"x": 320, "y": 160},
            "L4": {"x": 420, "y": 160},
            "P1": {"x": 120, "y": 260},
            "P2": {"x": 220, "y": 260},
            "P3": {"x": 320, "y": 260},
            "P4": {"x": 420, "y": 260}
        }
    }
}

# Employee codes for testing
MOCK_EMPLOYEE_CODES = [
    "EMP001",
    "EMP002",
    "EMP003",
    "EMP004",
    "EMP005"
]

# Process status simulation data
MOCK_PROCESS_STATUS = {
    "M0067": False,  # AUTO
    "M0068": False,  # HOME
    "M0076": False,  # 1st PULL PASS
    "M0085": False,  # 1st PULL NG
    "M0078": False,  # 2nd PULL PASS
    "M0087": False,  # 2nd PULL NG
    "M0075": False,  # TEST RESULT PASS
    "M0079": False   # TEST RESULT NG
}

def get_mock_test_data(lot_number_suffix="0001"):
    """Generate mock test data for testing"""
    from datetime import datetime
    
    return {
        "LOT_NUMBER": f"{datetime.now().strftime('%y%m%d')}001{lot_number_suffix}",
        "PART_NUMBER": "ALC001",
        "EMP_CODE": "EMP001",
        "TEST_DATE": datetime.now().strftime("%Y-%m-%d"),
        "TEST_TIME": datetime.now().strftime("%H:%M:%S"),
        "L1_VALUE": 12.5,
        "L2_VALUE": 10.2,
        "L3_VALUE": 15.1,
        "L4_VALUE": 12.0,
        "P1_VALUE": 6.8,
        "P2_VALUE": 5.6,
        "P3_VALUE": 7.9,
        "P4_VALUE": 4.7,
        "OVERALL_RESULT": "PASS",
        "FAILED_DEVICES": "",
        "TEST_DURATION": 45.5
    }

def get_simulated_process_cycle():
    """Get a simulated process cycle for testing"""
    return [
        ("M0067", "AUTO", True),
        ("M0068", "HOME", True),
        ("M0076", "1st PULL PASS", True),
        ("M0078", "2nd PULL PASS", True),
        ("M0075", "TEST RESULT PASS", True)
    ]

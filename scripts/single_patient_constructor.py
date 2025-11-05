import json
import sys

from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "data_api"))

from db_interfaces.fhir_objs.R5 import Patient, Identifier, FHIRDate, PatientCommunication

bday = datetime(1946, 1, 15).date()
bday_str = bday.isoformat()
date = FHIRDate(bday_str)


identifier = Identifier({'value': '5EHTt77xRGwYsu3oQt1uuA=='})

pc = PatientCommunication({"language": {"text": "English"}})

patient_data = {
    "gender": 'Male', 
    "communication": [{"language": {"text": "English"}}], 
    "birthDate": bday_str,
    "deceasedDateTime": None,
    "identifier": [{'value': '5EHTt77xRGwYsu3oQt1uuA=='}],
}

patient0 = Patient(patient_data)


import json

from datetime import datetime


class Patient:

    def __init__(self, kwargs):

        # c.f. https://build.fhir.org/patient.html
        # Also, unclear where extensions go.
        # - Race exists in https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-race.html
        # - Birthplace exists as http://hl7.org/fhir/extensions/StructureDefinition-patient-birthPlace.html

        # See also https://www.health-samurai.io/articles/extending-fhir-resources
        # for additional examples of extensions

        self.resourceType = "Patient"
        # from Resource: id, meta, implicitRules, and language
        # from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("identifier")  # An identifier for this patient
        self.active = kwargs.get(
            "active", None
        )  # Whether this patient's record is in active use
        self.name = kwargs.get("human_name", None)  # A name associated with the patient
        self.telecom = kwargs.get(
            "contact_point", None
        )  # A contact detail for the individual
        self.gender = (kwargs.get("gender", None),)  # male | female | other | unknown
        self.birthDate = (
            kwargs.get("birthdate", None),
        )  # The date of birth for the individual
        # self.deceased[x]: Indicates if the individual is deceased or not. One of these 2:
        deceased = kwargs.get("deceased_time", False)
        if not deceased:
            self.deceasedBoolean = deceased
        else:
            self.deceasedDateTime = (deceased,)
        self.address = kwargs.get("address", None)  # An address for the individual
        self.maritalStatus = kwargs.get(
            "CodeableConcept"
        )  # Marital (civil) status of a patient
        # self.multipleBirth[x]:  # Whether patient is part of a multiple birth. One of these 2:
        mulitple_birth = kwargs.get("multiple_birth", False)
        if not mulitple_birth:
            self.multipleBirthBoolean = mulitple_birth
        else:
            self.multipleBirthInteger = mulitple_birth
        self.photo = (kwargs.get("attachment", None),)  # Image of the patient
        self.contact = (kwargs.get("contacts", None),)
        # { # A contact party (e.g. guardian, partner, friend) for the patient
        # "relationship" : kwargs.get("codeable_concept", None), # The kind of relationship
        # "name" : kwargs.get("human_name", None), # A name associated with the contact person
        # "telecom" : kwargs.get("ContactPoint", None), # A contact detail for the person
        # "address" : kwargs.get("Address", None), # Address for the contact person
        # "gender" : kwargs.get("gender"), # male | female | other | unknown
        # "organization" : kwargs.get("Reference(Organization) }, # I Organization that is associated with the contact
        # "period" : kwargs.get("Period } # The period during which this contact person or organization is valid to be contacted relating to this patient
        # },
        self.communication = kwargs.get("communication_preference", None)
        # { # A language which may be used to communicate with the patient about his or her health
        # "language" = kwargs.get("CodeableConcept }, # R!  The language which can be used to communicate with the patient about his or her health
        # "preferred" : <boolean> # Language preference indicator
        # },
        self.generalPractitioner = kwargs.get("general_practitioner", None)
        # [{ Reference(Organization|Practitioner|PractitionerRole) }], # Patient's nominated primary care provider
        self.managingOrganization = kwargs.get("managing_organization", None)
        # { Reference(Organization) }, # Organization that is the custodian of the patient record
        self.link = kwargs.get("link", None)
        # [{ # Link to a Patient or RelatedPerson resource that concerns the same actual individual
        #     "other" : kwargs.get("Reference(Patient|RelatedPerson) }, # R!  The other patient or related person resource that the link refers to
        #     "type" : "<code>" # R!  replaced-by | replaces | refer | seealso
        # }]

    def to_json(self):
        return self.__dict__


class DiagnosticReport:

    def __init__(self, kwargs):

        # c.f. https://build.fhir.org/diagnosticreport.html

        self.resourceType = ("DiagnosticReport",)
        # from Resource: id, meta, implicitRules, and language
        # from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("identifier")  # Business identifier for report
        self.basedOn = kwargs.get("based_on", None)
        # Reference(CarePlan|ImmunizationRecommendation|MedicationRequest =tritionOrder|ServiceRequest) }]
        # What was requested
        self.status = kwargs.get("status", None)
        # R! Status: registered | partial | preliminary | modified | final | amended | corrected | appended | cancelled | entered-in-error | unknown
        self.category = kwargs.get("codeable_concept", None)  # Service category
        self.code = kwargs.get("codeable_concept")
        # R!  Name/Code for this diagnostic report
        self.subject = kwargs.get("subject", None)
        # Reference(
        #   BiologicallyDerivedProduct|Device|Group|Location|
        #   Medication|Organization|Patient|Practitioner|Substance
        # )
        # The subject of the report - usually, but not always, the patient
        self.encounter = (kwargs.get("encounter", None),)
        # Health care event when test ordered -> Reference(Encounter)
        # effective[x]: Clinically relevant time/time-period for report. One of these 2:
        effective = kwargs.get("effective_date", None)
        if type(effective) is datetime:
            self.effectiveDateTime = effective
        elif type(effective) is list or type(effective) is list:
            self.effectivePeriod = ([effective[0], effective[1]],)
        self.issued = kwargs.get("issued", None)
        # DateTime this version was made
        self.performer = kwargs.get("performer")
        # [{ Reference(CareTeam|Organization|Practitioner|PractitionerRole) }]
        # Responsible Diagnostic Service
        self.resultsInterpreter = kwargs.get("interpreter", None)
        # [{ Reference(CareTeam|Organization|Practitioner|PractitionerRole) }]
        # # Primary result interpreter
        self.specimen = kwargs.get("specimen", None)
        # Reference(Specimen)
        # Specimens this report is based on
        self.result = kwargs.get("result", None)
        # Reference(Observation)
        # I Observations
        self.note = kwargs.get(
            "annotation", None
        )  # Comments about the diagnostic report
        self.study = kwargs.get("study", None)
        # Reference to full details of an analysis associated with the diagnostic report
        # One of Reference(GenomicStudy|ImagingStudy)
        self.supportingInfo = kwargs.get("supporting_info", None)
        # [{ # Additional information supporting the diagnostic report
        # "type" : { CodeableConcept }, # R!  Supporting information role code icon
        # "reference" : { Reference(Citation|DiagnosticReport|Observation|Procedure) } # R!  Supporting information reference
        # }],
        self.media = kwargs.get("media", None)
        # [{ # Key images or data associated with this report
        # "comment" : "<string>", # Comment about the image or data (e.g. explanation)
        # "link" : { Reference(DocumentReference) } # R!  Reference to the image or data source
        # }],
        self.composition = (kwargs.get("composition", None),)
        # I Reference to a Composition resource for the DiagnosticReport structure
        # - Reference(Composition)
        self.conclusion = kwargs.get("conclusion")
        # Clinical conclusion (interpretation) of test results, SHOULD be markdown
        self.conclusionCode = (kwargs.get("conclusion_code", None),)
        # Codes for the clinical conclusion of test results
        # - CodeableConcept
        self.presentedForm = kwargs.get("attachment", None)
        # Entire report as issued - Attachment


class Organization:

    def __init__(self, kwargs):

        # c.f. https://build.fhir.org/organization.html

        self.resourceType = ("Organization",)
        # from Resource: id, meta, implicitRules, and language
        # from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get(
            "identifier"
        )  # Identifies this organization  across multiple systems
        self.active = kwargs.get(
            "active", None
        )  # Whether the organization's record is still in active use
        self.type = kwargs.get("codeable_concept", None)  # Kind of organization
        self.name = kwargs.get(
            "organization_name", None
        )  # I Name used for the organization
        self.alias = kwargs.get(
            "aliases", None
        )  # A list of alternate names that the organization is known as, or was known as in the past
        self.description = (
            kwargs.get("description_markdown", None),
        )  # Additional details about the Organization that could be displayed as further information to identify the Organization beyond its name
        self.contact = kwargs.get(
            "contact", None
        )  # Official contact details for the Organization
        self.partOf = kwargs.get(
            "part_of", None
        )  # The organization of which this organization forms a part
        self.endpoint = kwargs.get(
            "endpoints", None
        )  # Technical endpoints providing access to services operated for the organization
        self.qualification = kwargs.get(
            "qualifications", None
        )  # Qualifications, certifications, accreditations, licenses, training, etc. pertaining to the provision of care
        #     [{
        #     "[{
        #     "identifier" : [{ Identifier }], # An identifier for this qualification for the organization
        #     "code" : { CodeableConcept }, # R!  Coded representation of the qualification
        #     "period" : { Period }, # Period during which the qualification is valid
        #     "issuer" : { Reference(Organization) } # Organization that regulates and issues the qualification
        # }]

    def to_json(self):
        return json.dumps(self.__dict__)


class FamilyMemberHistory:

    def __init__(self, kwargs):

        # c.f. https://build.fhir.org/familymemberhistory.html

        self.resourceType = kwargs.get("FamilyMemberHistory", None)
        # from Resource: id, meta, implicitRules, and language
        # from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("identifier")  # External Id(s) for this record
        # vvv <canonical(PlanDefinition|Questionnaire|ActivityDefinition|Measure|OperationDefinition)>"
        self.instantiatesCanonical = kwargs.get(
            "cannonical", None
        )  # Instantiates FHIR protocol or definition
        self.instantiatesUri = kwargs.get(
            "uri", None
        )  # Instantiates external protocol or definition
        self.status = kwargs.get(
            "code"
        )  # R!  partial | completed | entered-in-error | health-unknown
        self.dataAbsentReason = kwargs.get(
            "codeable_concept", None
        )  # subject-unknown | withheld | unable-to-obtain | deferred
        self.patient = kwargs.get("patient")  # R!  Patient history is about
        self.date = (
            kwargs.get("date_time", None),
        )  # When history was recorded or last updated
        self.participant = kwargs.get("participant", None)
        # [{ # Who or what participated in the activities related to the family member history and how they were involved
        #     "function" : { CodeableConcept }, # Type of involvement
        #     "actor" : { Reference(CareTeam|Device|Organization|Patient|Practitioner|
        #     PractitionerRole|RelatedPerson) } # R!  Who or what participated in the activities related to the family member history
        # }],
        self.name = (kwargs.get("human_name"),)  # The family member described
        self.relationship = (
            kwargs.get("relationship"),
        )  # R!  Relationship to the subject icon
        self.sex = (kwargs.get("gender"),)  # male | female | other | unknown
        # born[x]: (approximate) date of birth. One of these 3:
        born = kwargs.get("born")
        if type(born) is str:
            self.bornString = (born,)
            # Unclear to me what the difference between strftime string and
            # "Old timey" (or whatever 'Period' is meant to imply)
            # self.bornPeriod = ...
        else:
            self.bornDate = (born,)
        # age[x]: (approximate) age. One of these 3:
        age = kwargs.get("age")
        if type(age) is int or type(age) is float:
            self.ageAge = age
        elif type(age) is list or type(age) is tuple:
            self.ageRange = [age[0], age[1]]  # Assume min/max range structure
        else:
            self.ageString = (age,)
        self.estimatedAge = (kwargs.get("estaimted_age", False),)  # I Age is estimated?
        # deceased[x]: Dead? How old/when?. One of these 5:
        deceased = kwargs.get("deceased", False)
        if not deceased:
            self.deceasedBoolean = deceased
        elif type(deceased) is int or type(deceased) is float:
            self.deceasedAge = deceased
        elif type(deceased) is list or type(deceased) is tuple:
            self.deceasedRange = [deceased[0], deceased[1]]
        elif type(deceased) is str:
            self.deceasedString = deceased
        elif type(deceased) is datetime:
            self.deceasedDate = deceased
        # Why was family member history performed?
        # FHIR considers the following acceptable reasons:
        # CodeableReference(AllergyIntolerance|Condition|DiagnosticReport|DocumentReference|Observation|QuestionnaireResponse)
        self.reason = kwargs.get("reason", None)
        self.note = kwargs.get("annotation", None)  # General note about related person
        self.condition = kwargs.get("relation_condition", None)
        # {# Condition that the related person had
        # "code" : { CodeableConcept }, # R!  Condition suffered by relation
        # "outcome" : { CodeableConcept }, # deceased | permanent disability | etc
        # "contributedToDeath" : <boolean>, # Whether the condition contributed to the cause of death
        # # onset[x]: When condition first manifested. One of these 4:
        # "onsetAge" : { Age },
        # "onsetRange" : { Range },
        # "onsetPeriod" : { Period },
        # "onsetString" : "<string>",
        # "note" : [{ Annotation }] # Extra information about condition
        # }],
        self.procedure = kwargs.get("relation_procedure", None)
        # [{ # Procedures that the related person had
        #     "code" : { CodeableConcept }, # R!  Procedures performed on the related person
        #     "outcome" : { CodeableConcept }, # What happened following the procedure
        #     "contributedToDeath" : <boolean>, # Whether the procedure contributed to the cause of death
        #     # performed[x]: When the procedure was performed. One of these 5:
        #     "performedAge" : { Age },
        #     "performedRange" : { Range },
        #     "performedPeriod" : { Period },
        #     "performedString" : "<string>",
        #     "performedDateTime" : "<dateTime>",
        #     "note" : [{ Annotation }] # Extra information about the procedure
        #     }]

    def to_json(self):
        return json.dumps(self.__dict__)


class GenomicStudy:

    def __init__(self, kwargs):

        # c.f. https://build.fhir.org/genomicstudy.html

        self.resourceType = ("GenomicStudy",)
        # from Resource: id, meta, implicitRules, and language
        # from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("identifier")  # Identifiers for this genomic study
        self.status = (
            kwargs.get("status"),
        )  # R!  registered | available | cancelled | entered-in-error | unknown
        self.type = kwargs.get(
            "codeable_concept"
        )  # The type of the study (e.g., Familial variant segregation, Functional variation detection, or Gene expression profiling)
        self.subject = kwargs.get("subject")  # See comment below
        # R!  The primary subject of the genomic study
        # Reference(
        #   BiologicallyDerivedProduct|Group|NutritionProduct|
        #   Patient|Substance
        # ) }
        self.encounter = kwargs.get(
            "encounter", None
        )  # The healthcare event with which this genomics study is associated
        self.startDate = kwargs.get("start_date")  # When the genomic study was started
        self.basedOn = kwargs.get(
            "based_on", None
        )  # Event resources that the genomic study is based on. Expected values are: Reference(ServiceRequest|Task)
        self.referrer = kwargs.get("referrer", None)
        # Healthcare professional who requested or referred the genomic study
        # Exepcted values are Reference(Practitioner|PractitionerRole)
        self.interpreter = kwargs.get("interpreter", None)
        # Healthcare professionals who interpreted the genomic study
        # Expected values: Reference(Practitioner|PractitionerRole)
        self.reason = kwargs.get("reason", None)
        # Why the genomic study was performed
        # Exepected values: CodeableReference(Condition|Observation)
        self.instantiatesCanonical = kwargs.get("cannonical_protocol", None)
        # The defined protocol that describes the study
        # Expected form: <canonical(PlanDefinition)>
        self.instantiatesUri = kwargs.get("uri", None)
        # The URL pointing to an externally maintained protocol that describes the study
        self.note = kwargs.get(
            "annotation", None
        )  # Comments related to the genomic study
        self.description = ("<markdown>",)  # Description of the genomic study
        self.analysis = kwargs.get("analysis_event", None)
        # [{ # Genomic Analysis Event
        # "identifier" : [{ Identifier }], # Identifiers for the analysis event
        # "methodType" : [{ CodeableConcept }], # Type of the methods used in the analysis (e.g., FISH, Karyotyping, MSI)
        # "changeType" : [{ CodeableConcept }], # Type of the genomic changes studied in the analysis (e.g., DNA, RNA, or AA change)
        # "genomeBuild" : { CodeableConcept }, # Genome build that is used in this analysis icon
        # "instantiatesCanonical" : "<canonical(PlanDefinition|ActivityDefinition)>", # The defined protocol that describes the analysis
        # "instantiatesUri" : "<uri>", # The URL pointing to an externally maintained protocol that describes the analysis
        # "title" : "<string>", # Name of the analysis event (human friendly)
        # "focus" : [{ Reference(Any) }], # What the genomic analysis is about, when it is not about the subject of record
        # "specimen" : [{ Reference(Specimen) }], # The specimen used in the analysis event
        # "date" : "<dateTime>", # The date of the analysis event
        # "note" : [{ Annotation }], # Any notes capture with the analysis event
        # "protocolPerformed" : { Reference(Procedure|Task) }, # The protocol that was performed for the analysis event
        # "regionsStudied" : [{ Reference(DocumentReference|Observation) }], # The genomic regions to be studied in the analysis (BED file)
        # "regionsCalled" : [{ Reference(DocumentReference|Observation) }], # Genomic regions actually called in the analysis event (BED file)
        # "input" : [{ # Inputs for the analysis event
        #     "file" : { Reference(DocumentReference) }, # File containing input data
        #     "type" : { CodeableConcept }, # Type of input data (e.g., BAM, CRAM, or FASTA)
        #     # generatedBy[x]: The analysis event or other GenomicStudy that generated this input file. One of these 2:
        #     "generatedByIdentifier" : { Identifier },
        #     "generatedByReference" : { Reference(GenomicStudy) }
        # }],
        self.output = kwargs.get("output")
        # [{ # Outputs for the analysis event
        #     "file" : { Reference(DocumentReference) }, # File containing output data
        #     "type" : { CodeableConcept } # Type of output data (e.g., VCF, MAF, or BAM)
        # }],
        self.performer = kwargs.get("performer", None)
        # [{ # Performer for the analysis event
        # "actor" : { Reference(Device|Organization|Practitioner|PractitionerRole) }, # The organization, healthcare professional, or others who participated in performing this analysis
        # "role" : { CodeableConcept } # Role of the actor for this analysis
        # }],
        self.device = kwargs.get("device", None)
        # [{ # Devices used for the analysis (e.g., instruments, software), with settings and parameters
        # "device" : { Reference(Device) }, # Device used for the analysis
        # "function" : { CodeableConcept } # Specific function for the device used for the analysis
        # }]

    def to_json(self):
        return json.dumps(self.__dict__)


if __name__ == "__main__":

    # Create a patient
    sample_props = {
        "human_name": "Jordan Taylor",
        "identifier": "Test-0001",
        "gender": "U",
    }
    patient = Patient(sample_props)

    print(f"Patient details: {patient.to_json()}")

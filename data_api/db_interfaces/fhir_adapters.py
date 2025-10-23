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


class Medication:
    # c.f. https://hl7.org/fhir/medication.html
    def __init__(self, kwargs):
        self.resourceType = "Medication",
        # // from Resource: id, meta, implicitRules, and language
        # // from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("", None)  # [{ Identifier }], // Business identifier for this medication
        self.code = kwargs.get("", None)  # { CodeableConcept }, // Codes that identify this medication
        self.status = kwargs.get("", None)  # "<code>", // active | inactive | entered-in-error
        self.marketingAuthorizationHolder = kwargs.get("", None)  # { Reference(Organization) }, // Organization that has authorization to market medication
        self.doseForm = kwargs.get("", None)  # { CodeableConcept }, // powder | tablets | capsule +
        self.totalVolume = kwargs.get("", None)  # { Quantity }, // When the specified product code does not infer a package size, this is the specific amount of drug in the product
        self.ingredient = kwargs.get("", None)  # [{ // Active or inactive ingredient
            #     "item" : { CodeableReference(Medication|Substance) }, # // R!  The ingredient (substance or medication) that the ingredient.strength relates to
            #     "isActive" : <boolean>, // Active ingredient indicator
            #     // strength[x]: Quantity of ingredient present. One of these 3:
            #     "strengthRatio" : { Ratio },
            #     "strengthCodeableConcept" : { CodeableConcept },
            #     "strengthQuantity" : { Quantity }
            # }],
        self.batch = kwargs.get("batch", None)
        ''' 
            {   // Details about packaged medications
                # "lotNumber" : "<string>", // Identifier assigned to batch
                # "expirationDate" : "<dateTime>" // When batch will expire
            },
        '''
        self.definition = kwargs.get("definition", None)  # { Reference(MedicationKnowledge) } // Knowledge about this medication

    def to_json(self):
        ...


class Encounter:
    
    def __init__(self, kwargs):

        # c.f. https://hl7.org/fhir/encounter.html

        self.resourceType = "Encounter"
        #   // from Resource: id, meta, implicitRules, and language
        #   // from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("", None) #  [{ Identifier }], // Identifier(s) by which this encounter is known
        self.status = kwargs.get("", None) #  "<code>", // R!  planned | in-progress | on-hold | discharged | completed | cancelled | discontinued | entered-in-error | unknown
        self.clazz = kwargs.get("", None) #  [{ CodeableConcept }], // Classification of patient encounter context - e.g. Inpatient, outpatient icon
        self.priority = kwargs.get("", None) #  { CodeableConcept }, // Indicates the urgency of the encounter icon
        self.type = kwargs.get("", None) #  [{ CodeableConcept }], // Specific type of encounter (e.g. e-mail consultation, surgical day-care, ...)
        self.serviceType = kwargs.get("", None) #  [{ CodeableReference(HealthcareService) }], // Specific type of service
        self.subject = kwargs.get("", None) #  { Reference(Group|Patient) }, // The patient or group related to this encounter
        self.subjectStatus = kwargs.get("", None) #  { CodeableConcept }, // The current status of the subject in relation to the Encounter
        self.episodeOfCare = kwargs.get("", None) #  [{ Reference(EpisodeOfCare) }], // Episode(s) of care that this encounter should be recorded against
        self.basedOn = kwargs.get("", None) 
        '''
            [{ Reference(CarePlan|DeviceRequest|ImmunizationRecommendation|
            MedicationRequest|NutritionOrder|RequestOrchestration|ServiceRequest|
            VisionPrescription) }], // The request that initiated this encounter
        '''
        self.careTeam = kwargs.get("", None)  # [{ Reference(CareTeam) }], // The group(s) that are allocated to participate in this encounter
        self.partOf = kwargs.get("", None)  # { Reference(Encounter) }, // Another Encounter this encounter is part of
        self.serviceProvider = kwargs.get("", None)  # { Reference(Organization) }, // The organization (facility) responsible for this encounter
        self.participant = kwargs.get("", None) 
        '''
            [{ // List of participants involved in the encounter
            "type" : [{ CodeableConcept }], // I Role of participant in encounter
            "period" : { Period }, // Period of time during the encounter that the participant participated
            "actor" : { Reference(Device|Group|HealthcareService|Patient|Practitioner|
            PractitionerRole|RelatedPerson) } // I The individual, device, or service participating in the encounter
            }],
        '''
        self.appointment = kwargs.get("", None)  # [{ Reference(Appointment) }], // The appointment that scheduled this encounter
        self.virtualService = kwargs.get("", None)  # [{ VirtualServiceDetail }], // Connection details of a virtual service (e.g. conference call)
        self.actualPeriod = kwargs.get("", None)  # { Period }, // The actual start and end time of the encounter
        self.plannedStartDate = kwargs.get("", None)  # "<dateTime>", // The planned start date/time (or admission date) of the encounter
        self.plannedEndDate = kwargs.get("", None)  # "<dateTime>", // The planned end date/time (or discharge date) of the encounter
        self.length = kwargs.get("", None)  # { Duration }, // Actual quantity of time the encounter lasted (less time absent)
        self.reason = kwargs.get("", None) 
        '''
            [{ // The list of medical reasons that are expected to be addressed during the episode of care
            "use" : [{ CodeableConcept }], // What the reason value should be used for/as
            "value" : [{ CodeableReference(Condition|DiagnosticReport|
            ImmunizationRecommendation|Observation|Procedure) }] // Reason the encounter takes place (core or reference)
            }],
        '''
        self.diagnosis = kwargs.get("", None) 
        '''
            [{ // The list of diagnosis relevant to this encounter
                "condition" : [{ CodeableReference(Condition) }], // The diagnosis relevant to the encounter
                "use" : [{ CodeableConcept }] // Role that this diagnosis has within the encounter (e.g. admission, billing, discharge …)
            }],
        '''
        self.account = kwargs.get("", None)  # [{ Reference(Account) }], // The set of accounts that may be used for billing for this Encounter
        self.dietPreference = kwargs.get("", None)  # [{ CodeableConcept }], // Diet preferences reported by the patient
        self.specialArrangement = kwargs.get("", None)  # [{ CodeableConcept }], // Wheelchair, translator, stretcher, etc
        self.specialCourtesy = kwargs.get("", None)  # [{ CodeableConcept }], // Special courtesies (VIP, board member)
        self.admission = kwargs.get("", None)  
        '''
            { // Details about the admission to a healthcare service
            "preAdmissionIdentifier" : { Identifier }, // Pre-admission identifier
            "origin" : { Reference(Location|Organization) }, // The location/organization from which the patient came before admission
            "admitSource" : { CodeableConcept }, // From where patient was admitted (physician referral, transfer)
            "reAdmission" : { CodeableConcept }, // Indicates that the patient is being re-admitted icon
            "destination" : { Reference(Location|Organization) }, // Location/organization to which the patient is discharged
            "dischargeDisposition" : { CodeableConcept } // Category or kind of location after discharge
            },
        '''
        self.location = kwargs.get("", None) 
        '''
        [{ // List of locations where the patient has been
            "location" : { Reference(Location) }, // R!  Location the encounter takes place
            "status" : "<code>", // planned | active | reserved | completed
            "form" : { CodeableConcept }, // The physical type of the location (usually the level in the location hierarchy - bed, room, ward, virtual etc.)
            "period" : { Period } // Time period during which the patient was present at the location
        }]
        '''
    
    def to_json(self):
        ...


class Flowsheet:
    
    # Initially unclear - see here
    # https://build.fhir.org/ig/HL7/uv-pocd/overview.html
    # see also: https://hl7.org/fhir/extensions/StructureDefinition-workflow-reason.html

    def __init__(self, kwargs):
        ...

    def to_json(self):
        ... 


class Procedure:

    def __init__(self, kwargs):

        # c.f. https://hl7.org/fhir/procedure.html

        self.resourceType = "Procedure"
        # // from Resource: id, meta, implicitRules, and language
        # // from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("", None)  # [{ Identifier }], // External Identifiers for this procedure
        self.instantiatesCanonical = kwargs.get("", None)  # ["<canonical(PlanDefinition|ActivityDefinition|Measure|OperationDefinition|Questionnaire)>"], // Instantiates FHIR protocol or definition
        self.instantiatesUri = kwargs.get("", None)  # ["<uri>"], // Instantiates external protocol or definition
        self.basedOn = kwargs.get("", None)  # [{ Reference(CarePlan|ServiceRequest) }], // A request for this procedure
        self.partOf = kwargs.get("", None)  # [{ Reference(MedicationAdministration|Observation|Procedure) }], // Part of referenced event
        self.status = kwargs.get("", None)  # "<code>", // R!  preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown
        self.statusReason = kwargs.get("", None)  # { CodeableConcept }, // Reason for current status
        self.category = kwargs.get("", None)  # [{ CodeableConcept }], // Classification of the procedure
        self.code = kwargs.get("", None)  # { CodeableConcept }, // Identification of the procedure
        self.subject = kwargs.get("", None)  # { Reference(Device|Group|Location|Organization|Patient|Practitioner) }, // R!  Individual or entity the procedure was performed on
        self.focus = kwargs.get("", None)
        '''
        { Reference(CareTeam|Group|Organization|Patient|Practitioner|
        PractitionerRole|RelatedPerson|Specimen) }, // Who is the target of the procedure when it is not the subject of record only
        '''
        self.encounter = kwargs.get("", None)  # { Reference(Encounter) }, // The Encounter during which this Procedure was created
        # // occurrence[x]: When the procedure occurred or is occurring. One of these 6:
        self.occurrenceDateTime = kwargs.get("", None)  # "<dateTime>",
        self.occurrencePeriod = kwargs.get("", None)  # { Period },
        self.occurrenceString = kwargs.get("", None)  # "<string>",
        self.occurrenceAge = kwargs.get("", None)  # { Age },
        self.occurrenceRange = kwargs.get("", None)  # { Range },
        self.occurrenceTiming = kwargs.get("", None)  # { Timing },
        self.recorded = kwargs.get("", None)  # "<dateTime>", // When the procedure was first captured in the subject's record
        self.recorder = kwargs.get("", None)  # { Reference(Patient|Practitioner|PractitionerRole|RelatedPerson) }, // Who recorded the procedure
        
        # // reported[x]: Reported rather than primary record. One of these 2:
        # TODO Flow control, because HL7 hates us and wants us miserable
        self.reportedBoolean = kwargs.get("", None)  # <boolean>,
        self.reportedReference = kwargs.get("", None)  # { Reference(Organization|Patient|Practitioner|PractitionerRole|RelatedPerson) },
        
        self.performer = kwargs.get("", None)
        '''
            [{ // Who performed the procedure and what they did
            "function" : { CodeableConcept }, // Type of performance
            "actor" : { Reference(CareTeam|Device|HealthcareService|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson) }, // I R!  Who performed the procedure
            "onBehalfOf" : { Reference(Organization) }, // I Organization the device or practitioner was acting for
            "period" : { Period } // When the performer performed the procedure
            }],
        '''
        self.location = kwargs.get("", None)  # { Reference(Location) }, // Where the procedure happened
        self.reason = kwargs.get("", None)  # [{ CodeableReference(Condition|DiagnosticReport|DocumentReference|Observation|Procedure) }], // The justification that the procedure was performed
        self.bodySite = kwargs.get("", None)  # [{ CodeableConcept }], // Target body sites
        self.outcome = kwargs.get("", None)  # { CodeableConcept }, // The result of procedure
        self.report = kwargs.get("", None)  # [{ Reference(Composition|DiagnosticReport|DocumentReference) }], // Any report resulting from the procedure
        self.complication = kwargs.get("", None)  # [{ CodeableReference(Condition) }], // Complication following the procedure
        self.followUp = kwargs.get("", None)  # [{ CodeableConcept }], // Instructions for follow up
        self.note = kwargs.get("", None)  # [{ Annotation }], // Additional information about the procedure
        self.focalDevice = kwargs.get("", None)
        '''
            [{ // Manipulated, implanted, or removed device
            "action" : { CodeableConcept }, // Kind of change to device
            "manipulated" : { Reference(Device) } // R!  Device that was changed
            }],
        '''
        self.used = kwargs.get("", None)  # [{ CodeableReference(BiologicallyDerivedProduct|Device|Medication|Substance) }], // Items used during procedure
        self.supportingInfo = kwargs.get("", None)  # [{ Reference(Any) }] // Extra information relevant to the procedure

    def to_json(self):
        ... 


class Registry:

    # Unclear what the appropriate model would be here
    def __init__(self, kwargs):
        ...

    def to_json(self):
        ... 


class Observation:

    # Using the "Observation" because "LabComponent" from EPIC Caboodle seems to fit here?
    # c.f. https://www.hl7.org/fhir/observation.html

    def __init__(self, kwargs):
        self.resourceType = "Observation"
        # // from Resource: id, meta, implicitRules, and language
        # // from DomainResource: text, contained, extension, and modifierExtension
        self.identifier = kwargs.get("", None)  # [{ Identifier }], // Business Identifier for observation
        
        # // instantiates[x]: Instantiates FHIR ObservationDefinition. One of these 2:
        instantiation = kwargs.get("observation", {})
        if not instantiation:
            raise Exception("---> Instantiation error: Instatiation must be dict of {canonical|reference}: definition <---")
        assert(len(list(instantiation.keys())) == 1), "Illegal instantiation provided"
        if "canonical" in instantiation.keys():
            self.instantiatesCanonical = "canonical"  # "<canonical(ObservationDefinition)>"
        elif "reference" in instantiation.keys():
            self.instantiatesReference = "reference"  # { Reference(ObservationDefinition) },
        elif "test"  in instantiation.keys():
            self.instantiatesCanonical = "{canonical|reference}"
        else:
            raise Exception("Illegal key provided")
        self.basedOn = kwargs.get("", None)  # [{ Reference(CarePlan|DeviceRequest|ImmunizationRecommendation|MedicationRequest|NutritionOrder|ServiceRequest) }], // Fulfills plan, proposal or order
        self.triggeredBy = kwargs.get("", None) 
        '''
            [{ // Triggering observation(s)
            "observation" : { Reference(Observation) }, // R!  Triggering observation
            "type" : "<code>", // R!  reflex | repeat | re-run
            "reason" : "<string>" // Reason that the observation was triggered
            }],
        '''
        self.partOf = kwargs.get("", None)  # [{ Reference(GenomicStudy|ImagingStudy|Immunization|MedicationAdministration|MedicationDispense|MedicationStatement|Procedure) }], // Part of referenced event
        self.status = kwargs.get("", None)  # "<code>", // R!  registered | preliminary | final | amended +
        self.category = kwargs.get("", None)  # [{ CodeableConcept }], // Classification of  type of observation
        self.code = kwargs.get("", None)  # { CodeableConcept }, // I R!  Type of observation (code / type)
        self.subject = kwargs.get("", None)  # { Reference(BiologicallyDerivedProduct|Device|Group|Location|Medication|NutritionProduct|Organization|Patient|Practitioner|Procedure|Substance) }, // Who and/or what the observation is about
        self.focus = kwargs.get("", None)  # [{ Reference(Any) }], // What the observation is about, when it is not about the subject of record
        self.encounter = kwargs.get("", None)  # { Reference(Encounter) }, // Healthcare event during which this observation is made
        
        # // effective[x]: Clinically relevant time/time-period for observation. One of these 4:
        # XXX: More FHIR pain
        '''
        "effectiveDateTime" : "<dateTime>",
        "effectivePeriod" : { Period },
        "effectiveTiming" : { Timing },
        "effectiveInstant" : "<instant>",
        '''

        self.issued = kwargs.get("", None)  # "<instant>", // Date/Time this version was made available
        self.performer = kwargs.get("", None)  # [{ Reference(CareTeam|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson) }], // Who is responsible for the observation
        
        # // value[x]: Actual result. One of these 13:
        # XXX: More FHIR pain (13)
        '''
        "valueQuantity" : { Quantity },
        "valueCodeableConcept" : { CodeableConcept },
        "valueString" : "<string>",
        "valueBoolean" : <boolean>,
        "valueInteger" : <integer>,
        "valueRange" : { Range },
        "valueRatio" : { Ratio },
        "valueSampledData" : { SampledData },
        "valueTime" : "<time>",
        "valueDateTime" : "<dateTime>",
        "valuePeriod" : { Period },
        "valueAttachment" : { Attachment },
        "valueReference" : { Reference(MolecularSequence) },
        '''
        self.dataAbsentReason = kwargs.get("", None)  # { CodeableConcept }, // I Why the result is missing
        self.interpretation = kwargs.get("", None)  # [{ CodeableConcept }], // High, low, normal, etc
        self.note = kwargs.get("", None)  # [{ Annotation }], // Comments about the observation
        self.bodySite = kwargs.get("", None)  # { CodeableConcept }, // I Observed body part
        self.bodyStructure = kwargs.get("", None)  # { Reference(BodyStructure) }, // I Observed body structure
        self.method = kwargs.get("", None)  # { CodeableConcept }, // How it was done
        self.specimen = kwargs.get("", None)  # { Reference(Group|Specimen) }, // Specimen used for this observation
        self.device = kwargs.get("", None)  # { Reference(Device|DeviceMetric) }, // A reference to the device that generates the measurements or the device settings for the device
        self.referenceRange = kwargs.get("", None)
        '''
            [{ // Provides guide for interpretation
            "low" : { Quantity(SimpleQuantity) }, // I Low Range, if relevant
            "high" : { Quantity(SimpleQuantity) }, // I High Range, if relevant
            "normalValue" : { CodeableConcept }, // Normal value, if relevant
            "type" : { CodeableConcept }, // Reference range qualifier
            "appliesTo" : [{ CodeableConcept }], // Reference range population
            "age" : { Range }, // Applicable age range, if relevant
            "text" : "<markdown>" // I Text based reference range in an observation
            }],
        '''
        self.hasMember = kwargs.get("", None)  # [{ Reference(MolecularSequence|Observation|QuestionnaireResponse) }], // Related resource that belongs to the Observation group
        self.derivedFrom = kwargs.get("", None)  # [{ Reference(DocumentReference|GenomicStudy|ImagingSelection|ImagingStudy|MolecularSequence|Observation|QuestionnaireResponse) }], // Related resource from which the observation is made
        self.component = kwargs.get("", None) 
        '''
            [{ // I Component results
            "code" : { CodeableConcept }, // I R!  Type of component observation (code / type)
            
            // value[x]: Actual component result. One of these 13:
            # XXX: More FHIR pain (13)
            "valueQuantity" : { Quantity },
            "valueCodeableConcept" : { CodeableConcept },
            "valueString" : "<string>",
            "valueBoolean" : <boolean>,
            "valueInteger" : <integer>,
            "valueRange" : { Range },
            "valueRatio" : { Ratio },
            "valueSampledData" : { SampledData },
            "valueTime" : "<time>",
            "valueDateTime" : "<dateTime>",
            "valuePeriod" : { Period },
            "valueAttachment" : { Attachment },
            "valueReference" : { Reference(MolecularSequence) },
            "dataAbsentReason" : { CodeableConcept }, // Why the component result is missing
            "interpretation" : [{ CodeableConcept }], // High, low, normal, etc
            "referenceRange" : [{ Content as for Observation.referenceRange }] // Provides guide for interpretation of component result
            }]
        '''

    def to_json(self):
        ... 


class CancerStaging:

    # see https://build.fhir.org/ig/HL7/fhir-mCODE-ig/StructureDefinition-mcode-cancer-stage-mappings.html
    # and https://terminology.hl7.org/5.1.0/CodeSystem-TNM.html

    def __init__(self, kwargs):
        ...

    def to_json(self):
        ... 


class Terminology:

    # see https://build.fhir.org/terminologies.html

    def __init__(self, kwargs):
        ...

    def to_json(self):
        ... 

if __name__ == "__main__":

    ### Patient creation stub
    '''
    # Create a patient
    sample_props = {
        "human_name": "Jordan Taylor",
        "identifier": "Test-0001",
        "gender": "U",
    }
    patient = Patient(sample_props)

    print(f"Patient details: {patient.to_json()}")
    '''
    objects = {
        "Patient": Patient(), 
        "DiagnosticReport": DiagnosticReport(), 
        "Organization": Organization(), 
        "FamilyMemberHistory": FamilyMemberHistory(), 
        "GenomicStudy": GenomicStudy(),
        "Medication": Medication(),
        "Encounter": Encounter(),
        "Procedure": Procedure(),
        "Observation": Observation(),
        }
    ### Object dump stub
    for name, obj in objects.items():
        print(f"{name}: {obj.__dict__.keys()}")
import time
import pandas as pd

def patients_from_df(data, converter):
    samples = []
    for df_row in data.itertuples(index=False):
        samples.append(converter["Patient"](df_row))
    return samples

def objects_from_single_df(
        data, fhir_item, patient_ids, converter, resource_url_strings=None
    ):
    # Handle the other way
    df = data['data']
    data_size = data['pagination']['sample_size'][0]
    ds = time.time()
    small_df = df[df["PatientDurableKey_e"].isin(patient_ids)]
    print(f"Data lookup required {time.time() - ds:.2f}")
    # print(f"Columns in order: ")
    # print("".join([f"- {idx}:{v} || " for idx, v in enumerate(df.columns)]))

    start = time.time()
    # print(f"Shape of {fhir_item} table: {small_df.shape} (original table size {df.shape})")
    samples = []
    for df_row in small_df.itertuples(index=False):
        p_refs = None if resource_url_strings is None else resource_url_strings.get(df_row.PatientDurableKey_e, None)
        if p_refs is None:
            samples.append(converter[fhir_item](df_row))
        else:
            samples.extend([converter[fhir_item](df_row, pr) for pr in p_refs])

    return samples

def catalog_objects_from_joint_df(data, fhir_item, converter):
    """Join and convert records for non-patient resources (e.g., Medication catalog)."""
    pt = data['data']['primary']
    join_config = data['config']
    foreign_key = join_config['fk']
    primary_table_name = join_config['primary_table']

    df = pt.rename(columns={
        col: f"{primary_table_name}__{col}"
        for col in pt.columns if col != foreign_key
    })
    for other_table_name, other_df in data['data'].items():
        if other_table_name == 'primary':
            continue
        renamed_other = other_df.rename(columns={
            col: f"{other_table_name}__{col}"
            for col in other_df.columns if col != foreign_key
        })
        df = pd.merge(df, renamed_other, on=foreign_key, how='inner')

    return [converter[fhir_item](df_row) for df_row in df.itertuples(index=False)]

def describe_object_fields(
    data, fhir_item, patient_ids, converter, resource_url_strings=None
    ):
    if fhir_item == "Procedure":
        pt = data['primary']
        unique_pcs = pt['ProcedureCodeSet'].unique()
        unique_codes = pt['ProcedureCode'].unique()
        print(f"Procedure: Found sets: {unique_pcs}\nCodes: {unique_codes[:5]}")
    elif fhir_item == "DiagnosticReport":
        dtd = data['DiagnosisTerminologyDim']
        nac = dtd['NameAndCode'].unique()
        g_nac = dtd['GroupedNameAndCode'].unique()
        tipo = dtd['Type'].unique()
        val = dtd['Value'].unique()

        print(f"Name and Code: {nac[:5]}")
        print(f"Grouped Name and Code: {g_nac[:5]}")
        print(f"T and V: {tipo} & {val[:5]}")
    elif fhir_item == "Encounter":
        print(f"---> Encounter Columns: {data.columns}")
    else:
        ...
    return None

def objects_from_joint_df(
        data, fhir_item, patient_ids, converter, resource_url_strings=None
    ):
    pt = data['data']['primary']
    join_config = data['config']
    foreign_key = join_config['fk']
    primary_table_name = join_config['primary_table']

    start = time.time()
    # Filter before renaming so bare column names are still available.
    small_df = pt[pt['PatientDurableKey_e'].isin(patient_ids)].copy()
    print(f"Data lookup with JOIN required {time.time() - start:.2f}")

    # Rename to Table__Column format (except the FK used for joining) so
    # itertuples field names match the SQL path namedtuple field names.
    small_df = small_df.rename(columns={
        col: f"{primary_table_name}__{col}"
        for col in small_df.columns if col != foreign_key
    })
    for other_table_name, other_df in data['data'].items():
        if other_table_name == 'primary':
            continue
        renamed_other = other_df.rename(columns={
            col: f"{other_table_name}__{col}"
            for col in other_df.columns if col != foreign_key
        })
        small_df = pd.merge(small_df, renamed_other, on=foreign_key, how='inner')

    samples = []
    patient_key = f"{primary_table_name}__PatientDurableKey_e"
    for df_row in small_df.itertuples(index=False):
        try:
            p_refs = None if resource_url_strings is None else resource_url_strings.get(
                getattr(df_row, patient_key), None
            )
        except Exception as e:
            print(f"ERROR: {e}")
            for k, v in resource_url_strings.items():
                print(f"{k}: {v}")
            raise
        if p_refs is None:
            samples.append(converter[fhir_item](df_row))
        else:
            samples.extend([converter[fhir_item](df_row, pr) for pr in p_refs])
    return samples
    
    # print(f"Processed {len(samples)} samples in {time.time() - start:.2f} s")
    # sample = samples[0].as_json()
    # print(f"Sample {sample}\n---> type {type(sample)}")
    # post_success = post_fhir_data(access_token, sample, fhir_item)
    # print(f"===> Success?\n{post_success}")


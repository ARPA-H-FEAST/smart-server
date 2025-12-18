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
    # Handle one way
    data_size = data['pagination']['sample_size']['primary'][0]
    counter = 0
    # print(f"Found sizes of:\n{data['pagination']}")
    pt = data['data']['primary']
    join_config = data['config']
    foreign_key = join_config['fk']

    start = time.time()
    small_df = pt[pt['PatientDurableKey_e'].isin(patient_ids)].copy()
    print(f"Data lookup with JOIN required {time.time() - start:.2f}")
    # print(f"----> Small df: {small_df}\nPrimaryTableColumns = {pt.columns}")
    # print(f"----> Join FK: {foreign_key}")
    # print(f"----> Small df shape: {small_df.shape}")
    for other_table_name, other_df in data['data'].items():
        if other_table_name == 'primary':
            continue
        # print(f"---> {other_table_name}: {other_df.shape}")
        small_df = pd.merge(small_df, other_df, on=foreign_key, how='inner')

    # print(f"---> {fhir_item}: Final joined shape - {small_df.shape} (original size {pt.shape})")
    samples = []
    for df_row in small_df.itertuples(index=False):
        try:
            p_refs = None if resource_url_strings is None else resource_url_strings.get(df_row.PatientDurableKey_e, None)
        except Exception as e:
            print(f"ERROR: {e}")
            for k, v in resource_url_strings.items():
                print(f"{k}: {v}")
            raise
        if p_refs is None:
            samples.append(converter[fhir_item](df_row))
        else:
            samples.extend([converter[fhir_item](df_row, pr) for pr in p_refs])
    # print(f"Sample for {len(patient_ids)} patients required {time.time() - start:.2f} seconds")
    return samples
    
    # print(f"Processed {len(samples)} samples in {time.time() - start:.2f} s")
    # sample = samples[0].as_json()
    # print(f"Sample {sample}\n---> type {type(sample)}")
    # post_success = post_fhir_data(access_token, sample, fhir_item)
    # print(f"===> Success?\n{post_success}")


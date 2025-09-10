import json
import requests
import time

DATA_BASE_URL = "http://localhost:8000/testing-ui/data-api/"
# DATA_BASE_URL = "https://feast.mgpc.biochemistry.gwu.edu/testing-ui/data-api/"


def get_data_sets():

    query_api = DATA_BASE_URL + "datasets/"
    response = requests.get(query_api)
    data = response.json()

    return data


def query_data_set_details(dataset_bco):

    query_api = DATA_BASE_URL + "dataset-metadata/"
    response = requests.post(query_api, json={"bcoid": dataset_bco})
    data = response.json()

    return data


def query_data_point(dataset_bco, sample_offset, limit):

    query_api = DATA_BASE_URL + "dataset-detail/"
    response = requests.post(query_api, 
        json={"bcoid": dataset_bco, "sample_limit": limit, "sample_offset": sample_offset}
    )

    data = response.json()

    return data


if __name__ == "__main__":

    data = get_data_sets()

    print("*"*80)
    print(f"---> Found data sets {data}")
    print("*"*80)

    sample_patient = {}

    datasets = data["results"]

    single_dataset_key = list(datasets.keys())[0]

    start = time.time()

    dataset_bco = single_dataset_key
    dataset = datasets[dataset_bco]

    print(f"{dataset_bco}: {dataset}")
    response = query_data_set_details(dataset_bco)

    print("*"*80)
    print(f"Dataset metadata response:")
    for k, v in response.items():
        print(f"{k}:\n{v}\n")
    print("*"*80)

    sample_offset = 0
    sample_limit = 50

    data = query_data_point(dataset_bco, sample_offset=sample_offset, limit=sample_limit)

    sample_data = data["db_entries"]
    metadata = data["db_metadata"]
    print("*"*80)
    print(f"Dataset sample response:")
    for k, v in data.items():
        if k == "db_entries":
            print(f"\nFound {len(v)} DB entries. Printing only the first sample.")
            print(f"{v[0]}\n")
        else:
            print(f"{k}:\n{v}\n")
    print("*"*80)

    sample_patient[dataset] = sample_data[0]

    print(f"Query roundtrip required {time.time() - start:.3f} s")

    print(sample_patient)

    # # Focus on NBCC data
    # dataset = datasets["FEAST_000012"]

    # # Focus on GWDC data
    # dataset = datasets["FEAST_000004"]

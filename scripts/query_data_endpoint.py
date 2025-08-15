import json
import requests
import time

DATA_BASE_URL = "http://localhost:8000/testing-ui/data-api/"


def get_data_sets():

    query_api = DATA_BASE_URL + "datasets/"
    response = requests.get(query_api)
    data = response.json()

    return data


def query_data_set_details(dataset_bco):

    query_api = DATA_BASE_URL + "dataset-metadata/"
    response = requests.post(query_api, json={"bcoid": dataset_bco})
    data = response.json()

    print(f"Query {dataset_bco}: Got:\n{data}")

    return data


def query_data_point(dataset_bco, start, stop):

    query_api = DATA_BASE_URL + "dataset-detail/"
    response = requests.post(query_api, json={"bcoid": dataset_bco, "format": "fhir"})

    print(f"Got response! {response}")

    data = response.json()

    return data


if __name__ == "__main__":

    data = get_data_sets()

    sample_patients = {}

    datasets = data["results"]
    start = time.time()
    for dataset_bco, dataset in datasets.items():
        print(f"{dataset_bco}: {dataset}")
        response = query_data_set_details(dataset_bco)

        data = query_data_point(dataset_bco, 0, 1)

        sample_data = data["db_entries"]
        metadata = data["db_metadata"]

        sample_patients[dataset] = sample_data[0]

        # print("*"*80)
        # print(f"============= {dataset}: SAMPLE DATA =============")
        # print(type(sample_data))
        # print("*"*80)
        # print(f"============= {dataset}: METADATA =============")
        # print(type(metadata))
        # print("*"*80)

    print(f"Query roundtrip required {time.time() - start:.3f} s")

    print(sample_patients)

    # # Focus on NBCC data
    # dataset = datasets["FEAST_000012"]

    # # Focus on GWDC data
    # dataset = datasets["FEAST_000004"]

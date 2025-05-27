from django.conf import settings

from data_api.models import BCOFileDescriptor

import json
import os
import sys

REL_PATH = "jsondb/bcodb/"
BCO_ROOT = settings.DATA_HOME / REL_PATH
TAR_PATH = settings.DATA_HOME / "tarballs/"
cwd = os.getcwd()

os.chdir(BCO_ROOT)

for bco_file in os.listdir():
    print(f"Working on {bco_file}")

    with open(os.path.join(BCO_ROOT, bco_file), "r") as fp:
        bco = json.load(fp)

    output_subdomain = bco["io_domain"]["output_subdomain"]
    description_domain = bco["description_domain"]

    filenames = []
    for output_object in output_subdomain:
        if "uri" in output_object.keys() and "filename" in output_object["uri"]:
            filenames.append(output_object["uri"]["filename"])
    if not filenames:
        print(f"---> Malformed BCO {bco_file}<--- : No associated filename found")
        continue
    keywords = description_domain.get("keywords", None)
    if not keywords or type(keywords) is not list:
        print(f"---> Malformed BCO {bco_file}<--- : Missing FEAST keywords")
        continue
    extension_domain = bco["extension_domain"]
    if len(extension_domain) > 1:
        print(f"---> Found extension domain of length {len(extension_domain)}")
        print(f"---> Extension domain content:\n{extension_domain}")
        sys.exit(1)
    extension_domain = extension_domain[0]
    dataset_extension = extension_domain.get("dataset_extension", None)
    if not dataset_extension:
        print(f"---> No FEAST information found, exiting")
        print(f"---> Extension domain content:\n{extension_domain}")
        sys.exit(2)

    # print(f"---> Got dataset values: {dataset_extension}")

    body_sites = dataset_extension.get("body_sites", None)
    print(f"---> Found body sites {type(body_sites)}")

    dataset_categories = dataset_extension.get("dataset_categories", None)
    print(f"---> Found dataset categories {type(dataset_extension)}")

    if not body_sites or not dataset_categories:
        print(
            f"---> Malformed BCO {bco_file}\nBody sites: {body_sites}\nDataset extension: {dataset_extension}"
        )
        sys.exit(3)

    usability_string = " ".join(bco["usability_domain"])
    if len(usability_string) > 497:
        usability_string = usability_string[:498] + "..."

    access_categories = []
    for dc in dataset_categories:
        if set(dc.keys()).intersection({"category_name", "category_value"}):
            access_categories.append({"name": dc["category_value"], "link": dc["category_faq"]})
    # print(f"*" * 80)
    # print(f"BCO Name: {bco_file}")
    # print(f"BCO path: {REL_PATH}/{bco_file}")
    # print(f"Described file: {filenames}")
    # print(f"Keywords found: {keywords}")
    # print(f"*" * 80)
    try:
        defaults = {
            "files_represented": filenames,
            "keywords": keywords,
            "body_sites": body_sites,
            "access_categories": access_categories,
            "usability_domain": usability_string,
        }
        BCOFileDescriptor.objects.update_or_create(
            bcoid=bco_file.strip(".json"),
            defaults=defaults,
        )
    except Exception as e:
        print("*" * 80)
        print("*" * 80)
        print(f"FATAL ERROR: {e}")
        print(f"...on BCO {bco_file}")
        print("---> MANUAL INTERVENTION REQUIRED <---")
        print("*" * 80)
        print("*" * 80)
        continue

os.chdir(cwd)

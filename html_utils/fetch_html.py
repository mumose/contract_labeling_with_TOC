#!/usr/bin/env python3

import os
import json
from bs4 import BeautifulSoup

import process_html


def main(html_file_dir, contract_name_map_path):
    """Defines Main Execution"""

    with open(contract_name_map_path, "r") as data:
        contract_map = json.load(data)
        contract_map = {v: k for k, v in contract_map.items()}

    print(contract_map)

    html_files = [x for x in os.listdir(html_file_dir)
                  if (x.endswith(".html") or x.endswith(".htm"))]
    data = {}
    for fname in html_files:
        if "Monsanto Company" in fname:
            continue

        html_input_path = os.path.join(html_file_dir, fname)
        with open(html_input_path, "r", encoding="latin1") as f:
            contents = f.read()

        contents = process_html.filter_contents(contents)
        s = BeautifulSoup(contents, "lxml")

        # process the html
        table = process_html.parse_html(s)

        basename = fname.split(".htm")[0]
        if basename not in contract_map:
            print(f"Filename: {basename}" +
                  "not found in contract map but HTML was parsed, skipping...")
            continue

        contract_uid = contract_map[basename]
        if not table:
            print(f"Filename: {basename} with File ID: {contract_uid}" +
                  "was parsed but contained no data, skipping..")
            continue

        data[contract_uid] = process_html.refine_table(table)

    return data


if __name__ == "__main__":
    fp = """/Users/shaan/My Drive/Master's DS/Capstone/project/multimodalContractSegmentation/cuad_htmls/"""
    contract_name_fp = "/Users/shaan/My Drive/Master's DS/Independent Study DSGA-1010/contract_labeling_with_TOC/contract_name_map.json"
    d = main(fp, contract_name_fp)
    print(d)

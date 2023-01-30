import process_html
from bs4 import BeautifulSoup
import json
import os


def main(html_file_dir, contract_name_map_path):
    """Defines Main Execution"""

    with open(
        contract_name_map_path,
        "r",
    ) as data:
        contract_map = json.load(data)
        contract_map = {v: k for k, v in contract_map.items()}
    print(contract_map)

    html_files = [x for x in os.listdir(html_file_dir) if x.endswith(".html")]
    data = {}
    for file in html_files:
        if "Monsanto Company" in file:
            continue
        with open(os.path.join(html_file_dir, file), "r", encoding="latin1") as f:
            contents = f.read()

        contents = process_html.filter_contents(contents)
        s = BeautifulSoup(contents, "lxml")
        table = process_html.parse_html(s)

        filename = file.split(".htm")[0]
        if filename not in contract_map:
            print(
                "Filename",
                filename,
                "not found in contract map but HTML was parsed, skipping..",
            )
            continue
        file_id = contract_map[filename]
        if not table:
            print(
                "Filename",
                filename,
                "with file id",
                file_id,
                "was parsed but contained no data, skipping..",
            )
            continue
        data[file_id] = process_html.refine_table(table)

    return data


if __name__ == "__main__":
    fp = """/Users/shaan/My Drive/Master's DS/Capstone/project/multimodalContractSegmentation/cuad_htmls/"""
    contract_name_fp = "/Users/shaan/My Drive/Master's DS/Independent Study DSGA-1010/contract_labeling_with_TOC/contract_name_map.json"
    d = main(fp, contract_name_fp)
    print(d)

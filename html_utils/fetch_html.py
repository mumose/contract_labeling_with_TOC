import os

import json
import yaml
import argparse
import pandas as pd
from tqdm import tqdm

from bs4 import BeautifulSoup
import sys

sys.path.append(os.path.abspath('./html_utils/'))

import process_html


# TODO: refactor so that this import is required. Each script should have
# standalone functionality that the main pipeline script uses when importing


def process_single_html(html_path, pipeline_config):
    """Reads in the HTML of the contract and postprocesses it

    Args:
        html_path: str. Path to the raw html to be processed
        pipeline_config: dict. Config containing user-defined params

    Returns:
        flattened_html_out: dict. Final html output after all
            postprocessing operations are applied to raw html
        html_out_savepath: str. The path to where the postprocessed html
            results are saved
    """

    html_config = pipeline_config["html_pipeline"]

    cuad_base_dir = pipeline_config["cuad_data_base_dir"]
    html_results_dir = html_config["processed_html_output_dir"]
    html_results_dir = os.path.join(cuad_base_dir, html_results_dir)

    if not os.path.exists(html_results_dir):
        os.makedirs(html_results_dir)

    html_path = os.path.join(cuad_base_dir, html_path)
    with open(html_path, "r", encoding="latin1") as f:
        contents = f.read()

    contents = process_html.filter_contents(contents)
    s = BeautifulSoup(contents, "lxml")

    # process the html
    table = process_html.parse_html(s)

    basename = os.path.basename(html_path)
    contract_uid, _ = os.path.splitext(basename)
    if not table:
        print(
            f"Filename: {basename} with File ID: {contract_uid} "
            + "was parsed but contained no data, skipping.."
        )

        toc_label_dict, html_out_savepath = None, None

    else:
        nested_html_out = process_html.refine_table(table)

        # flatten the processed html to obtain the final html result
        toc_label_dict = process_html.flatten_processed_html(nested_html_out)

        html_out_savepath = os.path.join(
            html_results_dir, f"{contract_uid}_processed_html.json"
        )

        with open(html_out_savepath, "w", encoding="utf-8") as json_fh:
            json.dump(toc_label_dict, json_fh, ensure_ascii=False, indent=2)

    return toc_label_dict, html_out_savepath


def main(input_df, pipeline_config):
    """Executes main execution of the html parsing pipeline

    Args:
        input_df: pd.DataFrame. The cuad_master_csv_mapping containing the
            paths the raw html files to be processed
        pipeline_config: dict. Config containing user-defined params

    Returns:
        None
    """

    # filter out rows that don't have a corresponding raw html
    valid_raw_html_cond = input_df["raw_html_path"].notnull()
    filter_df = input_df.loc[valid_raw_html_cond]

    for idx, (row_idx, row) in tqdm(enumerate(filter_df.iterrows())):
        _, html_out_savepath = process_single_html(
            row["raw_html_path"], pipeline_config
        )

        input_df.loc[row_idx, "processed_html_path"] = html_out_savepath

        # save the results intermittently
        if idx % 50 == 0:
            input_df.to_csv(
                pipeline_config["cuad_master_csv_mapping_path"], index=False
            )

    input_df.to_csv(pipeline_config["cuad_master_csv_mapping_path"], index=False)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pipeline_config",
        help="path to the pipeline config yaml file",
        default="./config/pipeline_config.yml",
    )

    args = parser.parse_args()

    with open(args.pipeline_config, "r") as yml_file:
        pipeline_config = yaml.load(yml_file, Loader=yaml.loader.SafeLoader)

    input_df = pd.read_csv(pipeline_config["cuad_master_csv_mapping_path"])

    main(input_df, pipeline_config)

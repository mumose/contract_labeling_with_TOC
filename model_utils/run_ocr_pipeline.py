import os
import json

import yaml
import argparse
import pandas as pd
from tqdm import tqdm

from doctr.io import DocumentFile
from doctr.models import ocr_predictor

# TODO: RUN OCR only for contracts that have a TOC

"""
    Must be executed from ./contract_labeling_with_TOC dir
    eg: python3 model_utils/run_ocr_pipeline.py
"""


def get_prediction(pipeline_config, pdf_path, contract_uid=None):
    """"""
    ocr_config = pipeline_config["ocr_pipeline"]

    cuad_base_dir = pipeline_config["cuad_data_base_dir"]
    ocr_results_dir = ocr_config["ocr_output_dir"]
    ocr_results_dir = os.path.join(cuad_base_dir, ocr_results_dir)

    if not os.path.exists(ocr_results_dir):
        os.makedirs(ocr_results_dir)

    pdf_path = os.path.join(cuad_base_dir, pdf_path)
    print(f"ocr_result_savepath={pdf_path}")

    # fetch the contract_uid from the pdf path
    # the cotract must have the basename of the form ct_xx.pdf
    # else provide a contract_uid
    if not contract_uid:
        contract_basname = os.path.basename(pdf_path)
        contract_uid, _ = os.path.splitext(contract_basname)

    # define the model object
    model = ocr_predictor(
        det_arch=ocr_config["text_detr_model"],
        reco_arch=ocr_config["text_recog_model"],
        pretrained=True,
    )

    # define the input data object
    doc = DocumentFile.from_pdf(pdf_path)

    # get the model pred
    model_pred = model(doc)

    # convert the model result to json and store
    json_output = model_pred.export()

    # define the outpath for this pdf file
    ocr_result_savepath = os.path.join(
        ocr_results_dir, f"{contract_uid}_ocr_results.json"
    )
    print(f"ocr_result_savepath={ocr_result_savepath}")

    with open(ocr_result_savepath, "w", encoding="utf-8") as json_fh:
        json.dump(json_output, json_fh, ensure_ascii=False, indent=2)

    return ocr_result_savepath


def main(input_df, pipeline_config):
    """Executes ocr 'pipeline for all contracts in master csv mapping"""
    # TODO: remove later if necessary
    # the html must be present
    raw_html_cond = input_df['raw_html_path'].notnull()

    # the OCR results must not be present
    ocr_results_cond = input_df['ocr_results_path'].isnull()

    filter_df = input_df.loc[(raw_html_cond) & (ocr_results_cond)]
    for idx, (row_idx, row) in tqdm(enumerate(filter_df.iterrows()),
                                    total=len(filter_df)):
        ocr_result_path = get_prediction(pipeline_config,
                                         row['pdf_path'])

        input_df.loc[row_idx, "ocr_results_path"] = ocr_result_path

        # save the results intermittently
        # if idx % 50 == 0:
        input_df.to_csv(pipeline_config["cuad_master_csv_mapping_path"],
                        index=False)

    input_df.to_csv(pipeline_config["cuad_master_csv_mapping_path"],
                    index=False)

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

    # call main function
    main(input_df, pipeline_config)

import os
import json
import yaml
import argparse

import pandas as pd
from tqdm import tqdm

from html_utils import fetch_html
from model_utils import postprocess_ocr_output
from pipeline_utils import match_toc_labels
from pipeline_utils import merge_bboxes
from pipeline_utils import visualize_results

# TODO: replace pipeline_results_path to pipeline_results_csv_path and
# pipeline_results_json_path


def save_pipeline_outputs(match_metadata_df,
                          pipeline_output_json,
                          pipeline_results_dir,
                          contract_uid):
    '''Saves the pipeline results to disk

    Args:
        match_metadata_df: pd.DataFrame. The results df obtained after
            running the matching pipeline
        pipeline_output_json: dict. The output structured in the manner
            required by the demo website
        pipeline_results_dir: str. The dir where the pipeline results will be
            saved
        contract_uid: str. The unique identifier for the contract
            the matching pipeline

    Returns:
        match_metadata_savepath: str. The path where the results df from the
            matching pipeline will be saved
        json_savepath: str. The path where the output structured in the manner
            required by the demo website will be saved
    '''

    contract_results_dir = os.path.join(pipeline_results_dir, contract_uid)
    if not os.path.exists(contract_results_dir):
        os.makedirs(contract_results_dir)

    # save the match metadata
    match_metadata_savepath = os.path.join(contract_results_dir,
                                           f"{contract_uid}_match_metadata.csv")

    match_metadata_df.to_csv(match_metadata_savepath, index=False)

    # save the json format of the pipeline results
    json_savepath = os.path.join(contract_results_dir,
                                 f"{contract_uid}.json")

    with open(json_savepath, 'r') as json_fh:
        json.dump(pipeline_output_json, json_fh)

    return match_metadata_savepath, json_savepath


def run_matching_single_contract(row, pipeline_config):
    '''Executes the pipeline for a single contract

    Args:
        row: pd.Series. Single row from the cuad metadata df
        pipeline_config: dict. Config containing user-defined params

    Returns:
        match_metadata_savepath: str. The path where the results df from the
            matching pipeline will be saved
        json_savepath: str. The path where the output structured in the manner
            required by the demo website will be saved
    '''
    ocr_config = pipeline_config['ocr_pipeline']
    toc_match_config = pipeline_config['toc_matching_pipeline']

    cuad_base_dir = pipeline_config['cuad_data_base_dir']

    pipeline_results_dir = pipeline_config["pipeline_results_dir"]
    pipeline_results_dir = os.path.join(cuad_base_dir, pipeline_results_dir)

    if not os.path.exists(pipeline_results_dir):
        os.makedirs(pipeline_results_dir)

    # get the contract_uid for this contract
    contract_uid = row['contract_uid']

    '''
    ***************************************************************************
                            HTML PIPELINE
    ***************************************************************************
    '''
    # postprocess the raw html file
    html_path = os.path.join(cuad_base_dir, row['raw_html_path'])

    toc_label_dict, html_out_savepath = \
        fetch_html.process_single_html(html_path,
                                       pipeline_config)

    '''
    ***************************************************************************
                            OCR PIPELINE
    ***************************************************************************
    '''
    # fetch the OCR results for this contract
    ocr_results_path = os.path.join(cuad_base_dir,
                                    row['ocr_results_path'])

    with open(ocr_results_path, 'r') as json_fh:
        raw_ocr_results = json.load(json_fh)

    # pass the ocr through postprocessing ops to get linewise OCR output
    linewise_ocr_output = \
        postprocess_ocr_output.get_linewise_ocr_output(raw_ocr_results,
                                                       ocr_config['ocr_line_merge_iou_threshold'])

    # convert to df and then sort by page id and y coord of the top left corner
    linewise_ocr_output_df = pd.DataFrame(linewise_ocr_output)
    linewise_ocr_output = \
        (
            linewise_ocr_output_df.sort_values(by=['page_id', 'ymin_min'])
            .to_dict(orient='list')
        )

    '''
    ***************************************************************************
                            MATCHING PIPELINE
    ***************************************************************************
    '''
    # now perform the fuzzy match between the TOC labels and the ocr output
    match_metadata = match_toc_labels.find_all_match_ids(toc_match_config,
                                                         toc_label_dict,
                                                         linewise_ocr_output)

    # conver to df and rename the cols
    match_metadata_df = pd.DataFrame(match_metadata)

    columns = {
                    0: 'Line1 via OCR',
                    1: 'Line2 via OCR',
                    2: 'Section Title via HTML',
                    3: 'ymin',
                    4: 'ymax',
                    5: 'page_id',
                    6: 'bboxes',
              }
    match_metadata_df = match_metadata_df.rename(columns=columns)

    # extract the exact text matches of the ocr text segments and the toc
    # labels
    (match_metadata_df['exact_match_bbox'],
     match_metadata_df['exact_match_text']) = zip(
            *match_metadata_df.apply(
                 lambda row: merge_bboxes.extract_exact_match(row),
                 axis=1
             )
         )

    '''
    ***************************************************************************
                         RESULTS VISUALIZATION PIPELINE
    ***************************************************************************
    '''
    pipeline_output_json = \
        visualize_results.viz_results_single_contract(pipeline_config,
                                                      match_metadata_df,
                                                      contract_uid)

    '''
    ***************************************************************************
                            SAVE PIPELINE OUTPUTS
    ***************************************************************************
    '''
    match_metadata_savepath, json_savepath = \
        save_pipeline_outputs(match_metadata_df,
                              pipeline_output_json,
                              pipeline_results_dir,
                              contract_uid)

    return match_metadata_savepath, json_savepath


def main(input_df, pipeline_config):
    """Main execution of the end-to-end pipeline"""
    # filter out contracts that don't have ocr results or that don't have
    # raw htmls
    ocr_results_cond = input_df['ocr_results_path'].notnull()
    raw_html_cond = input_df['raw_html_path'].notnull()

    filter_df = input_df.loc[(ocr_results_cond) | (raw_html_cond)]

    for idx, (row_idx, row) in tqdm(enumerate(filter_df.iterrows())):
        match_metadata_savepath, json_savepath = \
            run_matching_single_contract(row, pipeline_config)

        # update the input df
        input_df.loc[row_idx, 'pipeline_results_csv_path'] = \
            match_metadata_savepath

        input_df.loc[row_idx, 'pipeline_results_json_path'] = json_savepath

        # save the results intermittently
        if idx % 50 == 0:
            input_df.to_csv(pipeline_config['cuad_master_csv_mapping_path'],
                            index=False)

    input_df.to_csv(pipeline_config['cuad_master_csv_mapping_path'],
                    index=False)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--pipeline_config',
                        help='path to the pipeline config yaml file',
                        default='./config/pipeline_config.yml')

    args = parser.parse_args()

    with open(args.pipeline_config, 'r') as yml_file:
        pipeline_config = yaml.load(yml_file, Loader=yaml.loader.SafeLoader)

    input_df = pd.read_csv(pipeline_config['cuad_master_csv_mapping_path'])

    # call main function
    main(input_df, pipeline_config)


#TODO: save the pipeline results df in the contract_pipeline_results/contract_uid dir

def run_matching_single_contract():
    '''
    Executes the pipeline for a single contract
    '''

def run_matching(contract_key, section_dicts, path_dict):
    section_dict = section_dicts[path_dict["section_dict_key"]]
    section_dict = flatten_contract_dict(section_dict)
    doctr_output_path = path_dict["doctr_output_json"]

    with open(doctr_output_path, 'r') as f:
        doctr_output = json.load(f)

    file_as_dict = get_file_by_dict(doctr_output)
    preprocessed_output = final_file_line_by_line(file_as_dict, threshold=0.65)
    df = pd.DataFrame(preprocessed_output)
    preprocessed_output = df.sort_values(by=['page_id', 'ymin_min']).to_dict(orient='list')

    df = pd.DataFrame(get_starts_all(section_dict, preprocessed_output)).rename(columns={0:'Line via OCR',
                                                                                         1:'Line2 via OCR',
                                         2:'Section Title via HTML',
                                         3:'ymin',
                                         4:'ymax',
                                         5:'page_id',
                                         6:'bboxes'})
    df['exact_match_bbox'], df['exact_match_text'] = zip(*df.apply(lambda row: extract_exact_match(row), axis=1))
    return df


def main():
    # section_dicts from fetch_html.main
    # fetch docTR outputs
    # run_matching_single_contract
    # merge_bboxes
    # exact match
    # viz results

#!/usr/bin/env python3

import sys
import os
import cv2
import shutil
import PIL
import math
from pdf2image import convert_from_path, convert_from_bytes


def convert_pdf2image(config, contract_uid, results_df):
    '''Converts the PDF version of the contract to individual images

    Args:
        config: dict
        contract_uid: str
        results_df: pd.DataFrame

    Returns:
        full_contract_image_dir: str
        contract_tracker: dict

    '''

    # refactor this code block with new master csv mapping logic
    '''
    pdf_name = pdf_path.split("/")[-1][:-4]

    contract_name = contract_name_mapper_reverse[pdf_name]
    full_output_folder = parent_path + contract_name + "/raw_images"

    pdf_save_dir = os.path.join(parent_path, contract_name, "contract_pdf")
    html_save_dir = os.path.join(parent_path, contract_name, "contract_html")
    '''
    cuad_data_base_dir = config["cuad_data_base_dir"]
    results_viz_config = config["results_viz_config"]

    pdf_path = results_df.loc[contract_uid, 'pdf_path']
    pdf_path = os.path.join(cuad_data_base_dir, pdf_path)

    # create a dir for each contract to store the converted images and
    # annotated images
    results_base_dir = results_viz_config['results_base_dir']
    results_base_dir = os.path.join(results_base_dir, contract_uid)
    if not os.path.exists(results_base_dir):
        os.makedirs(results_base_dir)

    # pylint: disable=E501
    full_contract_image_dir = os.path.join(results_base_dir,
                                           results_viz_config['full_contract_image_dir'])
    if not os.path.exists(full_contract_image_dir):
        os.makedirs(full_contract_image_dir)

        print("*" * 50)
        print(f"Saving converted pdf2image results in {full_contract_image_dir}")
        print("*" * 50)

    annotated_image_dir = os.path.join(results_base_dir,
                                       results_viz_config['annotated_image_dir'])
    if not os.path.exists(annotated_image_dir):
        os.makedirs(annotated_image_dir)

        print("*" * 50)
        print(f"Saving annotated image results in {annotated_image_dir}")
        print("*" * 50)

    # convert the pdf to images
    convert_from_path(pdf_path=pdf_path,
                      output_folder=full_contract_image_dir,
                      poppler_path=results_viz_config['poppler_path'],
                      fmt=results_viz_config['image_fmt'],
                      dpi=results_viz_config['image_dpi'],
                      hide_annotations=True)

    img_files = os.listdir(full_contract_image_dir)

    page_tracking = {
                        'dimensions': None,
                        'bbox': None,
                        'path_to_raw_image': None,
                        'path_to_annotated_image': None,
                     }

    pages_list = []
    for img_name in img_files:
        pages_list.append(page_tracking.copy())

        raw_image_path = os.path.join(full_contract_image_dir, img_name)
        pages_list[-1]['path_to_raw_image'] = raw_image_path

        # TODO: replace this line with cv2 ops
        pages_list[-1]['dimensions'] = PIL.Image.open(raw_image_path).size

    contract_tracker = {contract_uid: {'pages': pages_list}}

    return full_contract_image_dir, contract_tracker


def write_bbox_images(pdf_parsed_df,
                      full_output_folder,
                      contract_tracker,
                      contract_uid):
    '''
    Returns json outpath file with info
    '''
    num_pages = len(contract_tracker[contract_uid]['pages'])
    for page_id in range(num_pages):
        if page_id not in pdf_parsed_df['page_id'].to_list():
            continue
        sub_df = df[df['page_id'] == page_id].reset_index(drop=True).copy()

        img_page_id = f"{page_id + 1}.jpg"
        img_name = list(filter(lambda x: True if img_page_id in x else False, os.listdir(full_output_folder)))[0]
        img_read_path = full_output_folder + "/" + img_name
        bbox_output_folder = full_output_folder[:-11]
        img_write_parent_path = f"{bbox_output_folder}/annotated_images/"

        if not os.path.exists(img_write_parent_path):
            os.mkdir(img_write_parent_path)

        img_write_full_path = img_write_parent_path + img_name
        img = cv2.imread(img_read_path)
        width, height = PIL.Image.open(img_read_path).size

        bbox_attributes = {'corr':None, 'text_via_ocr':None, 'text_from_html':None}
        contract_tracker[contract_uid]['pages'][page_id]['bbox'] = [bbox_attributes.copy() for _ in range(len(sub_df))]
        contract_tracker[contract_uid]['pages'][page_id]['path_to_image_with_bounding_box'] = img_write_full_path

        for idx, row in sub_df.iterrows():
            (x1, y1), (x2, y2) = row['exact_match_bbox']

            x1 = math.floor(width * x1)
            x2 = math.ceil(width * x2)
            y1 = math.floor(height * y1)
            y2 = math.ceil(height * y2)

            img = cv2.rectangle(img, (x1, y1), (x2, y2), (255,0,0), 2)
            print(f"Drew bounding boxes for {img_name} page ")

            contract_tracker[contract_uid]['pages'][page_id]['bbox'][idx]['corr'] = ((x1, y1), (x2, y2))
            contract_tracker[contract_uid]['pages'][page_id]['bbox'][idx]['text_via_ocr'] = row['exact_match_text']
            contract_tracker[contract_uid]['pages'][page_id]['bbox'][idx]['text_from_html'] = row['Section Title via HTML']

        cv2.imwrite(img_write_full_path, img)
        print(f"Wrote image with bboxes @ {img_write_full_path}")

    return contract_tracker
import os
import shutil
import math

import cv2
from pdf2image import convert_from_path

"""
CHANGES
- changed image dimensions to H x W from W x H
- changed path_to_image_with_bounding_box to path_to_annotated_image
- changed images with bbox to annotated_image_dir
- changed corr to coords

"""


def prepare_results_dir(pipeline_config,
                        row,
                        contract_uid):
    """Creates the necessary dir structure for saving the pipeline outputs

    Args:
        pipeline_config: dict. Config containing user-defined params
        row: pd.DataFrame. Row from the cuad master csv mapping df that
            corresponds to the given contract
        contract_uid: str. The unique identifier for the contract
            the matching pipeline

    Returns:
        pdf_path: str. Path to the input pdf
        html_path: str. Path to the input raw html
        full_contract_image_dir: str. Dir where the images obtained
            after pdf2image conversion will be saved
        annotated_image_dir: str. Dir where the images annotated with the
            pipeline outputs will be saved
        input_pdf_dst_path: str. Path in the results dir
            where the input pdf is saved
        input_html_dst_path: str. Path in the results dir
            where the input html is saved

    """
    results_viz_config = pipeline_config["visualize_results_pipeline"]

    cuad_base_dir = pipeline_config["cuad_data_base_dir"]

    pipeline_results_dir = pipeline_config["pipeline_results_dir"]
    pipeline_results_dir = os.path.join(cuad_base_dir, pipeline_results_dir)

    if not os.path.exists(pipeline_results_dir):
        os.makedirs(pipeline_results_dir)

    # create dir to store the output for this specific contract
    # the output will consist of two subdirs. One for the converted images
    # and the other for the annotated images
    contract_results_dir = os.path.join(pipeline_results_dir, contract_uid)
    if not os.path.exists(contract_results_dir):
        os.makedirs(contract_results_dir)

    # create the dir to store the converted images
    full_contract_image_dir = os.path.join(
        contract_results_dir, results_viz_config["full_contract_image_dir"]
    )

    if not os.path.exists(full_contract_image_dir):
        os.makedirs(full_contract_image_dir)

    # create the dir to store the annotated images
    annotated_image_dir = os.path.join(
        contract_results_dir, results_viz_config["annotated_image_dir"]
    )

    if not os.path.exists(annotated_image_dir):
        os.makedirs(annotated_image_dir)

    # copy the pdf and html to the results dir
    # we do this so that the output is compatible with the demo website
    # for displaying the results
    input_pdf_save_dir = os.path.join(
        contract_results_dir, results_viz_config["input_pdf_save_dir"]
    )
    if not os.path.exists(input_pdf_save_dir):
        os.makedirs(input_pdf_save_dir)

    # copy the input pdf over to the results dir
    pdf_path = row['pdf_path']
    pdf_path = os.path.join(cuad_base_dir, pdf_path)

    pdf_basename = os.path.basename(pdf_path)

    input_pdf_dst_path = os.path.join(input_pdf_save_dir, pdf_basename)
    shutil.copy(pdf_path, input_pdf_dst_path)

    # create the dir for the input_html in the results dir
    input_html_save_dir = os.path.join(
        contract_results_dir, results_viz_config["input_html_save_dir"]
    )

    if not os.path.exists(input_html_save_dir):
        os.makedirs(input_html_save_dir)

    # copy the input html over to the results dir
    html_path = row['raw_html_path']
    html_path = os.path.join(cuad_base_dir, html_path)

    html_basename = os.path.basename(html_path)

    input_html_dst_path = os.path.join(input_html_save_dir, html_basename)
    shutil.copy(html_path, input_html_dst_path)

    return (
        pdf_path,
        html_path,
        full_contract_image_dir,
        annotated_image_dir,
        input_pdf_dst_path,
        input_html_dst_path,
    )


def convert_pdf2image(pipeline_config, pdf_path, full_contract_image_dir):
    """Converts the PDF version of the contract to individual images

    Args:
        pipeline_config: dict. Config containing user-defined params
        pdf_path: str. Path to the input pdf
        full_contract_image_dir: str. Dir where the images obtained
            after pdf2image conversion will be saved

    Returns:
        None
    """

    results_viz_config = pipeline_config["visualize_results_pipeline"]

    # convert the pdf to images
    convert_from_path(
        pdf_path=pdf_path,
        output_folder=full_contract_image_dir,
        poppler_path=results_viz_config["poppler_path"],
        fmt=results_viz_config["image_fmt"],
        dpi=results_viz_config["image_dpi"],
        hide_annotations=True,
    )

    return


def create_contract_tracker(
    full_contract_image_dir,
    annotated_image_dir,
    input_pdf_dst_path,
    input_html_dst_path,
    contract_uid,
):
    """Creates the basic JSON output data structure for saving the
        pipeline outputs

    Args:
        full_contract_image_dir: str. Dir where the images obtained
            after pdf2image conversion will be saved
        annotated_image_dir: str. Dir where the images annotated with the
            pipeline outputs will be saved
        input_pdf_dst_path: str. Path in the results dir
            where the input pdf is saved
        input_html_dst_path: str. Path in the results dir
            where the input html is saved
        contract_uid: str. The unique identifier for the contract

    Returns:
        contract_tracker: dict. The output structured in the manner
            required by the demo website
    """

    # search over image dir obtained after pdf2image conversion
    converted_img_files = os.listdir(full_contract_image_dir)

    # create the page level info data structure required in the demo website
    page_tracking = {
        "dimensions": None,
        "bbox": None,
        "path_to_raw_image": None,
        "path_to_annotated_image": None,
    }

    pages_list = []
    for img_name in converted_img_files:
        pages_list.append(page_tracking.copy())

        raw_image_path = os.path.join(full_contract_image_dir, img_name)
        pages_list[-1]["path_to_raw_image"] = raw_image_path

        img_size = cv2.imread(raw_image_path).shape
        img_dimensions = img_size[:2]  # dimensions are H x W
        pages_list[-1]["dimensions"] = img_dimensions

    # create the contract tracker obj to save the JSON results of the
    # pipeline
    contract_tracker = {
        contract_uid: {
            "pages": pages_list,
            "raw_pdf_dir": input_pdf_dst_path,
            "raw_html_dir": input_html_dst_path,
            "full_contract_image_dir": full_contract_image_dir,
            "annotated_image_dir": annotated_image_dir,
        }
    }

    return contract_tracker


def annotate_images(match_results_df,
                    full_contract_image_dir,
                    annotated_image_dir,
                    contract_tracker,
                    contract_uid):
    """Annotates the contract images and exports the pipeline results as JSON

    Args:
        match_results_df: pd.DataFrame. Obtained after running the matching
            pipeline
        full_contract_image_dir: str. The dir containing the images
            obtained after pdf2image conversion
        annotated_image_dir: str. Dir where the images annotated with the
            pipeline outputs will be saved
        contract_tracker: dict. The output structured in the manner
            required by the demo website
        contract_uid: str. The unique identifier for the contract

    Returns:
        contract_tracker: dict. The output structured in the manner
            required by the demo website
    """
    num_pages = len(contract_tracker[contract_uid]["pages"])

    for page_id in range(num_pages):
        # if the page doesn't have any bboxes to annoated the images with
        if page_id not in match_results_df['page_id'].to_list():
            continue

        page_id_cond = match_results_df['page_id'] == page_id
        subset_df = match_results_df[page_id_cond].reset_index(drop=True).copy()

        img_page_id = f"{page_id + 1}.jpg"
        img_name = list(
            filter(
                lambda x: True if img_page_id in x else False,
                os.listdir(full_contract_image_dir),
            )
        )[0]

        img_in_path = os.path.join(full_contract_image_dir, img_name)
        img_out_path = os.path.join(annotated_image_dir, img_name)

        img = cv2.imread(img_in_path)
        height, width = img.shape[:2]  # dimensions are H x W

        bbox_attributes = {"coords": None, "text_via_ocr": None, "text_from_html": None}

        contract_tracker[contract_uid]["pages"][page_id]["bbox"] = [
            bbox_attributes.copy() for _ in range(len(subset_df))
        ]

        contract_tracker[contract_uid]["pages"][page_id][
            "path_to_annotated_image"
        ] = img_out_path

        for idx, row in subset_df.iterrows():
            (x1, y1), (x2, y2) = row["exact_match_bbox"]

            x1 = math.floor(width * x1)
            x2 = math.ceil(width * x2)
            y1 = math.floor(height * y1)
            y2 = math.ceil(height * y2)

            img = cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)

            contract_tracker[contract_uid]["pages"][page_id]["bbox"][idx]["coords"] = (
                (x1, y1),
                (x2, y2),
            )

            contract_tracker[contract_uid]["pages"][page_id]["bbox"][idx][
                "text_via_ocr"
            ] = row["exact_match_text"]

            contract_tracker[contract_uid]["pages"][page_id]["bbox"][idx][
                "text_from_html"
            ] = row["Section Title via HTML"]

        cv2.imwrite(img_out_path, img)

    return contract_tracker


def viz_results_single_contract(pipeline_config,
                                cuad_master_csv_row,
                                match_results_df,
                                contract_uid):
    """Main Execution

    Args:
        pipeline_config: dict. Config containing user-defined params
        cuad_master_csv_row: pd.Series. Row from the cuad master csv
            corresponding to the given contract
        match_results_df: pd.DataFrame. The results dataframe obtained after running
        contract_uid: str. The unique identifier for the contract
            the matching pipeline

    Returns:
        contract_tracker: dict. The output structured in the manner
            required by the demo website
    """
    # create the required dir structure in the results folder
    # copy the input pdf and html over
    (pdf_path,
     html_path,
     full_contract_image_dir,
     annotated_image_dir,
     input_pdf_dst_path,
     input_html_dst_path) = prepare_results_dir(pipeline_config,
                                                cuad_master_csv_row,
                                                contract_uid)

    # convert the input pdf to images
    convert_pdf2image(pipeline_config, pdf_path, full_contract_image_dir)

    # create the contract tracker for exporting results as JSON
    contract_tracker = create_contract_tracker(
        full_contract_image_dir,
        annotated_image_dir,
        input_pdf_dst_path,
        input_html_dst_path,
        contract_uid,
    )

    # annotate the images with the pipeline output
    contract_tracker = annotate_images(match_results_df,
                                       full_contract_image_dir,
                                       annotated_image_dir,
                                       contract_tracker,
                                       contract_uid)

    return contract_tracker

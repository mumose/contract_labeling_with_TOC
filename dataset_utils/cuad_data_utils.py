#!/usr/bin/env python3

import os
from pathlib import Path
import pandas as pd

from IPython.display import display

"""
Creates master_csv mapping for CUAD dataset. Creates unique
id for each contract and maps it to filepaths of different data
artifacts in the CUAD dataset

ENSURE YOU CHANGE THE CURRENT WORKING DIR TO THE SAME LEVEL AS
THE CUAD DATASET DIR (i.e ./CUAD_v1)

Usage: python3 cuad_data_utils.py
"""

# TODO: Do we need to store the division of the contracts into parts
# eg: Part I, Part II, etc

# define some global params used in the process
cuad_base_path = "CUAD_v1/"
assert os.path.isdir(cuad_base_path), (
    "ENSURE THIS SCRIPT IS RUN IN THE PARENT OF CUAD (i.e. ./CUAD_v1). "
    + "IT IS NECESSARY FOR THE RELATIVE FILEPATHS IN THE MAPPING"
)

# define the base dirs for the various filelists
cuad_pdf_path = "CUAD_v1/full_contract_pdf/"
cuad_txt_path = "CUAD_v1/full_contract_txt/"
cuad_raw_html_path = "CUAD_v1/contract_raw_html/"
cuad_processed_html_path = "CUAD_v1/contract_processed_html/"
cuad_ocr_results_path = "CUAD_v1/contract_ocr_results/"
cuad_pipeline_results_path = "CUAD_v1/contract_pipeline_results/"

master_csv_savepath = os.path.join(cuad_base_path, "cuad_master_csv_mapping.csv")

# define the extensions we perform a search over to create the filelists
pdf_extensions = ["*.pdf", "*.PDF"]
txt_extensions = ["*.txt"]
raw_html_extensions = ["*.html", "*.htm"]


def get_cuad_fnames(
    extensions, search_path, cuad_base_path, is_exists, master_df, col_name
):
    """Returns list of filepaths with given extensions relative to basepath

    Args:
        extensions: List[str]. List of extensions to search for
        search_path: str. The parent dir path from where you
            want to perform your search
        cuad_base_path: str. Base path of cuad required. Filenames will
            be fetched relative to this path
        is_exists: bool. Flag specifying if the master_csv was already
            present when the pipeline was run or if it being created from
            scratch
        master_df: pd.DataFrame. csv mapping for cuad dataset
        col_name: str. The csv mapping column for which we are fetching files

    Returns:
        fnames: List[str]. List of filenames with given extensions
            relative to cuad_base_path
    """
    fnames = []

    total_count, ext_count = 0, 0
    for ext in extensions:
        for path in Path(search_path).rglob(ext):
            fnames.append(path.relative_to(cuad_base_path).as_posix())

        total_count = len(fnames)
        ext_count = total_count - ext_count
        print(f"Total Num of Files with {ext} Extension: {ext_count}")

    print(f"\nTotal Num of Files Found: {total_count}")

    if is_exists:
        print(
            "\nmaster_csv already exists "
            + "Removing files that have already been matched"
        )

        existing_files = master_df.loc[:, col_name].tolist()

        new_files = set(fnames) - set(existing_files)
        fnames = list(new_files)

    print(
        "\nTotal Num of Files Found After Removing "
        + f"Duplicates from master_csv: {len(fnames)}"
    )

    print(f"\nFilepath format: {fnames[0] if fnames else 'No files present!'}")
    print("*" * 100)

    return fnames


def fetch_filelists(master_df, is_exists):
    """Fetches the pdf, txt and raw_html filelists for CUAD contracts

    Args:
        master_df: pd.DataFrame. csv mapping for cuad dataset
        is_exists: bool. Flag specifying if the master_csv was already
            present when the pipeline was run or if it being created from
            scratch

    Returns:
        pdf_paths: List[str]. List of pdf filepaths in CUAD
        txt_paths: List[str]. List of txt filepaths in CUAD
        raw_html_paths: List[str]. List of raw html filepaths in CUAD
    """
    # fetch the pdf filelist
    print(f"Fetching filepaths for PDF files. Num Extensions: {len(pdf_extensions)}\n")
    pdf_paths = get_cuad_fnames(
        pdf_extensions, cuad_pdf_path, ".", is_exists, master_df, "pdf_path"
    )

    # fetch the txt filelist
    print(f"Fetching filepaths for txt files. Num Extensions: {len(txt_extensions)}\n")
    txt_paths = get_cuad_fnames(
        txt_extensions, cuad_txt_path, ".", is_exists, master_df, "txt_path"
    )

    # fetch the raw html filelist
    print(
        f"Fetching filepaths for HTML files. Num Extensions: {len(raw_html_extensions)}\n"
    )
    raw_html_paths = get_cuad_fnames(
        raw_html_extensions,
        cuad_raw_html_path,
        ".",
        is_exists,
        master_df,
        "raw_html_path",
    )

    return pdf_paths, txt_paths, raw_html_paths


def match_filepath_to_contract(master_df, filepaths, col_name):
    """Performs fuzzy match to link txt path with contract_uid

    This function is used as part of a pandas.apply op

    Args:
        master_df: pandas.DataFrame. Maps contract_ids to contract metadata
        filepaths: List[str]. List of paths to match. Can be .txt, .html, etc
        col_name: str. Name of the col you want to update, eg: 'txt_path'

    Returns:
        master_df: pandas.DataFrame. Maps contract_ids to contract metadata.
            Additional column 'col_name' is added
    """
    print(f"\nFound {len(filepaths)} to match for {col_name}")

    mismatch_count = 0
    mismatch_fnames = []
    for path in filepaths:
        file_basename = os.path.splitext(os.path.basename(path))[0]

        # match on the basenames for the pdf and filepaths
        # using pd.Series.str.contains results in incorrect matches
        # such as ct_1 and ct_10. ct_1 would match with both
        match_cond = master_df["contract_basename"] == file_basename

        if not match_cond.any():
            mismatch_count += 1
            mismatch_fnames.append(path)
        else:
            master_df.loc[match_cond, col_name] = path
            if col_name.startswith("txt"):
                match_status_col = "is_txt_matched"
            else:
                match_status_col = "is_raw_html_matched"

            # update the flag to indicate the match was successful
            master_df.loc[match_cond, match_status_col] = True

    # check for mismatches in file matching
    if mismatch_count:
        print(f"MATCHING FOR {col_name.upper()} WAS NOT SUCCESSFUL")
        print(
            "Number of files that were not matched "
            + f"successfully: {mismatch_count} out of "
            + f"{len(filepaths)} files. Printing files below"
        )

        print("\n\tFilepath: " + "\n\tFilepath: ".join(mismatch_fnames))
        print("*" * 100)
    else:
        print(f"All {col_name} files matched successfully!\n")
        print("*" * 100)

    """
    Assert statement to check if the number of matched files matches the number
    of input files. Due to inconsistencies in the way the CUAD dataset
    stores files, some files have minor variations in their filename
    for different formats leading to incorrect matches so the assert would fail
    instead we keep track of them using the is_txt_matched and
    is_raw_html_matched columns
    """

    # test if all the filepaths have been matched or if they were
    # already renamed
    # define cond for finding rows that are not null
    # not_null_cond = master_df.loc[:, col_name].notnull()

    # assert master_df.loc[not_null_cond, col_name].count() == len(filepaths), \
    #     "master_df was not updated successfully!" + \
    #     f"\nNum Not Null Entries: {master_df.loc[not_null_cond, col_name].count()}" + \
    #     f"\nLength of filelist: {len(filepaths)}"

    return master_df


def create_cuad_master_csv(pdf_paths, txt_paths, raw_html_paths, is_exists, master_df):
    """Creates the master_csv mapping.

    Defines empty df with required columns and then populates them.
    Finally saves the master_csv mapping in the CUAD base directory

    Args:
        pdf_paths: List[str]. List of pdf filepaths in CUAD
        txt_paths: List[str]. List of txt filepaths in CUAD
        raw_html_paths: List[str]. List of raw html filepaths in CUAD
        is_exists: bool. Flag specifying if the master_csv was already
            present when the pipeline was run or if it being created from
            scratch
        master_df: pd.DataFrame. csv mapping for cuad dataset

    Returns:
        None
    """
    # create empty df with columns to be populated.
    # use var other than master_df to account for case master_df already exists
    # the bool cols are by default False
    df = pd.DataFrame()
    df = df.assign(
        contract_uid=None,
        contract_type=None,
        dataset=None,
        contract_basename=None,
        pdf_path=None,
        is_pdf_renamed=False,
        txt_path=None,
        is_txt_matched=False,
        is_txt_renamed=False,
        raw_html_path=None,
        is_raw_html_matched=False,
        is_raw_html_renamed=False,
        processed_html_path=None,
        ocr_results_path=None,
        pipeline_results_path=None,
    )
    # sort the pdf paths in alphabetical order.
    # These are used to create contract_uids
    pdf_paths.sort(reverse=False)

    df["pdf_path"] = pdf_paths

    # create the contract_uid based on the row_number of the contract
    # contract IDs are of the form ct_xx
    if is_exists:
        # sort by contract uids and find the final one
        master_df = master_df.sort_values(by=["contract_uid"], ascending=True)
        last_contract_uid = master_df.tail(1).loc[:, "contract_uid"].iloc[0]
        last_contract_uid_int = int(last_contract_uid.split("_")[-1])

        # get the numerical value of each of the new contract_ids
        contract_uids = list(
            range(last_contract_uid_int, last_contract_uid_int + len(pdf_paths))
        )

        df["contract_uid"] = contract_uids
        df["contract_uid"] = df["contract_uid"].apply(lambda row: f"ct_{row}")

    else:
        # if creating from scratch then use the index number
        df["contract_uid"] = df.index + 1
        df["contract_uid"] = df["contract_uid"].apply(lambda row: f"ct_{row}")

    # populate the contract type column
    df["contract_type"] = df["pdf_path"].apply(lambda row: row.split("/", 4)[-2])

    # specify which dataset this is
    df["dataset"] = "cuad"

    # create a col with just the basename of the contracts.
    # Used in associating the contract_ids with other filepaths
    df["contract_basename"] = df["pdf_path"].apply(
        lambda row: os.path.splitext(os.path.basename(row))[0]
    )

    # set bool cols to have False as default val
    bool_cols = [
        "is_pdf_renamed",
        "is_txt_matched",
        "is_txt_renamed",
        "is_raw_html_matched",
        "is_raw_html_renamed",
    ]
    df.loc[:, bool_cols] = False

    if is_exists:
        # concat the new df to the existing master_df
        # there might be new txt_paths, html_paths that did not
        # match with pdf_paths in the first run and so we match on the
        # entire master_df and not just the new files
        master_df = pd.concat([master_df, df], axis=0)
        master_df = master_df.reset_index(drop=True)
        master_df = master_df.sort_values(by=["contract_uid"])

    else:
        # if no master_df exists then rename the new df and pass along
        # for matching
        master_df = df.copy()

    # match the txt_paths to the contract_uids
    print("Matching txt_filepaths to contract_uids\n")
    master_df = match_filepath_to_contract(master_df, txt_paths, "txt_path")

    # match the raw_html_paths to the contract_uids
    print("Matching raw_html_filepaths to contract_uids\n")
    master_df = match_filepath_to_contract(master_df, raw_html_paths, "raw_html_path")

    return master_df


def rename_files(row, col_name):
    """Renames the file on disk and updates the master_csv

    If the filepath in 'col_name' is None, we return None
    Only files for which the is_txt_matched and is_raw_html_matched columns
    are True will be renamed.

    Args:
        row: pd.Series. Single row of master_df mapping

    Returns:
        updated_path: str. Updated path with the contract_uid in
            place of the file's basename
    """
    contract_uid = row["contract_uid"]
    old_path = row[col_name]

    # if the txt path was not matched successfully return the old name.
    # Skip renaming
    if col_name == "txt_path" and not row["is_txt_matched"]:
        return old_path, False

    # if the raw_html path was not matched successfully return the old name.
    # Skip renaming
    if col_name == "raw_html_path" and not row["is_raw_html_matched"]:
        return old_path, False

    updated_path = None
    # rename only the entries that are non-null
    if isinstance(old_path, str):
        # create updated path with contract_uid in place of file's basename
        old_path_parent_dir = os.path.dirname(old_path)
        file_ext = os.path.splitext(old_path)[-1]

        updated_path = os.path.join(old_path_parent_dir, f"{contract_uid}{file_ext}")

        try:
            # rename the file on disk
            os.rename(old_path, updated_path)
            return updated_path, True

        except FileNotFoundError:
            # if the file is not found, likely due to the pipeline being run
            # before, then catch the error and pass
            print(f"FILE NOT FOUND: old_path: {old_path}")
            return old_path, False

    return updated_path, False


def prepare_data_dir(master_df):
    """Prepares the data dirs by creating the reqd subdirs and renaming files

    Args:
        master_df: pd.DataFrame. csv mapping for cuad dataset

    Returns:
        None
    """

    print("Creating Necessary Directory Structure\n")
    if not os.path.exists(cuad_pdf_path):
        os.makedirs(cuad_pdf_path)

    if not os.path.exists(cuad_pdf_path):
        os.makedirs(cuad_txt_path)

    if not os.path.exists(cuad_raw_html_path):
        os.makedirs(cuad_raw_html_path)

    if not os.path.exists(cuad_processed_html_path):
        os.makedirs(cuad_processed_html_path)

    if not os.path.exists(cuad_ocr_results_path):
        os.makedirs(cuad_ocr_results_path)

    if not os.path.exists(cuad_pipeline_results_path):
        os.makedirs(cuad_pipeline_results_path)

    print("Successfully Created Necessary Directory Structure")
    print("*" * 100)

    print("Renaming Files\n")
    print("Renaming pdf filenames\n")
    master_df["pdf_path"], master_df["is_pdf_renamed"] = zip(
        *master_df.apply(lambda row: rename_files(row, "pdf_path"), axis=1)
    )
    print("Finished renaming pdf paths!")
    print("*" * 100)

    print("Renaming txt filenames\n")
    master_df["txt_path"], master_df["is_txt_renamed"] = zip(
        *master_df.apply(lambda row: rename_files(row, "txt_path"), axis=1)
    )

    print("Finished renaming txt paths!")
    print("*" * 100)

    print("Renaming raw_html filenames\n")
    master_df["raw_html_path"], master_df["is_raw_html_renamed"] = zip(
        *master_df.apply(lambda row: rename_files(row, "raw_html_path"), axis=1)
    )

    print("Finished renaming raw_html paths!")
    print("*" * 100)

    master_df = master_df.sort_values(by=["contract_uid"])

    print(f"Saving master_csv at {master_csv_savepath}\n")
    master_df.to_csv(master_csv_savepath, index=False, header=True)
    print(f"Successfully saved master_csv at {master_csv_savepath}!\n")

    print("Displaying Counts of Non-Null Entries\n")
    display(master_df.isnull().sum())

    print("*" * 100)
    display(master_df["is_txt_matched"].value_counts())
    print("*" * 100)

    print("*" * 100)
    display(master_df["is_txt_renamed"].value_counts())
    print("*" * 100)

    print("*" * 100)
    display(master_df["is_raw_html_matched"].value_counts())
    print("*" * 100)

    print("*" * 100)
    display(master_df["is_raw_html_renamed"].value_counts())
    print("*" * 100)

    return master_df


def main():
    """Defines Main Execution"""

    # check if the master_csv alredy exists. It implies that the
    # pipeline is being re-run (possibly for new files)
    if os.path.exists(master_csv_savepath):
        print("master_csv exists..., updating mapping for any new files")

        # update the flag to indicate that the master_csv already exists
        is_exists = True

        # read the existing master_df from disk
        master_df = pd.read_csv(master_csv_savepath)
    else:
        print("master_csv not present. Creating a new one")
        is_exists, master_df = False, None

    # fetch the various filelists by globing over defined global params
    pdf_paths, txt_paths, raw_html_paths = fetch_filelists(master_df, is_exists)

    # create and populate master csv. Finally save the mapping to disk
    master_df = create_cuad_master_csv(
        pdf_paths, txt_paths, raw_html_paths, is_exists, master_df
    )

    # create the reqd subdirs and rename the filepaths.
    # update the master_csv once filenames are renamed
    master_df = prepare_data_dir(master_df)

    return


if __name__ == "__main__":
    print("\n" + "*" * 100)
    print(" Processing... ".center(100, "*"))
    print("*" * 100 + "\n")

    main()
    print("\n" + "*" * 100)
    print(" Finished Processing ".center(100, "*"))
    print("*" * 100 + "\n")

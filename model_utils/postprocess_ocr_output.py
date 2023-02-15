def get_word_level_ocr_output(raw_ocr_output):
    """Parses OCR output into dict to better represent the data

    Args:
        raw_ocr_output: dict. Raw JSON results obtained from OCR pipeline

    Returns:
        word_level_ocr_output: dict. OCR results parsed into word level
            representations
    """
    word_level_ocr_output = {
        "words": [],
        "ymin_ymax": [],
        "page_id": [],
        "page_dimensions": [],
        "is_next_line_merge": [],
        "bboxes": [],
    }

    # loop through the json output of OCR and store in the new dict
    for page in raw_ocr_output["pages"]:
        for block in page["blocks"]:
            for idx, line in enumerate(block["lines"]):
                ((xmin, ymin), (xmax, ymax)) = line["geometry"]

                word_level_ocr_output["words"].append(
                    [line["words"][i]["value"] for i in range(len(line["words"]))]
                )

                word_level_ocr_output["bboxes"].append(
                    [line["words"][i]["geometry"] for i in range(len(line["words"]))]
                )

                word_level_ocr_output["ymin_ymax"].append((ymin, ymax))
                word_level_ocr_output["page_id"].append(page["page_idx"])

                word_level_ocr_output["page_dimensions"].append(page["dimensions"])

    return word_level_ocr_output


def getIOU(segment1, segment2, threshold):
    """Defines merging algorithm for line geometries.

    If lines are in different blocks but have similar line coordinates,
    we will be able to "merge" them as one line this way.
    Function needed because OCR model does not always treat the same line
    as an item within the same block

    Args:
        segment1: List[int, int]. The top-left and bottom-right coords of the
            first segment we're looking at
        segment2: List[int, int]: The top-left and bottom-right coords of the
            second segment we're looking at
        threshold: float. The minimum IOU overlap required to merge two
            segments

    Returns:
        is_line_merge_next: bool. Flag specifying if the two segments should be
            merged
    """
    ymin1, ymax1 = segment1
    ymin2, ymax2 = segment2

    # get the lesser of the y_min and y_max coords
    lesser_ymax = min(ymax1, ymax2)
    lesser_ymin = min(ymin1, ymin2)

    # get the greatr of the y_min and y_max coords
    greater_ymax = max(ymax1, ymax2)
    greater_ymin = max(ymin1, ymin2)

    intersection = lesser_ymax - greater_ymin

    # no overlap
    if intersection < 0:
        return False

    union = greater_ymax - lesser_ymin

    if (intersection / union) > threshold:
        return True

    return False


def get_line_ids_to_merge(word_level_ocr_output, threshold):
    """Determines if two successive word-level segments should be merged

    Args:
        word_level_ocr_output: dict. OCR results parsed into word level
            representations
        threshold: float. The minimum IOU overlap required to merge two
            segments

    Returns:
        lines_to_merge_indices: List[Tuple(int, int)]. List of indices of
            pairs of word-level segments that need to be merged
    """

    lines_to_merge_indices = []
    for i in range(len(word_level_ocr_output["words"])):

        for j in range(i + 1, len(word_level_ocr_output["words"])):
            page_id_cond = (
                word_level_ocr_output["page_id"][i]
                == word_level_ocr_output["page_id"][j]
            )

            if page_id_cond and getIOU(
                word_level_ocr_output["ymin_ymax"][i],
                word_level_ocr_output["ymin_ymax"][j],
                threshold,
            ):
                lines_to_merge_indices.append((i, j))

    return lines_to_merge_indices


def merge_lines(lines_to_merge_indices):
    """Creates dict mapping of overlapping segments to merge

    Args:
        lines_to_merge_indices: List[Tuple(int, int)]. List of indices of
            pairs of word-level segments that need to be merged

    Returns:
        lines: dict
        follows: dict
    """

    lines = dict()
    follows = dict()

    for i, j in lines_to_merge_indices:
        if i not in lines:
            if i not in follows:
                lines[i] = [i, j]
                follows[j] = [i]

            else:
                one_link_back = follows[i][0]

                while one_link_back in follows:
                    one_link_back = follows[one_link_back][0]

                if j not in lines[one_link_back]:
                    lines[follows[i][0]].append(j)
        else:
            lines[i].append(j)

        if j not in follows:
            follows[j] = [i]

        else:
            follows[j].append(i)

    return lines, follows


def get_linewise_ocr_output(raw_ocr_output, threshold):
    """Merges word-level segments from OCR into line-level segments

    Args:
        raw_ocr_output: dict. Raw JSON results obtained from OCR pipeline
        threshold: float. The minimum IOU overlap required to merge two
            segments

    Returns:
        linewise_ocr_output: dict. OCR results obtained after merging
            overlapping word-level segments into contiguous segments
    """
    # get the word level ocr output from the raw ocr results
    word_level_ocr_output = get_word_level_ocr_output(raw_ocr_output)

    # define the line-level ocr output dict
    linewise_ocr_output = {
        "full_line": [],
        "page_id": [],
        "ymax_max": [],
        "ymin_min": [],
        "bboxes": [],
    }

    # get the indices of the word-level segments to merge
    lines_to_merge = get_line_ids_to_merge(word_level_ocr_output, threshold)

    # get the map of the indices to merge
    line_merge_map, follow_merge_map = merge_lines(lines_to_merge)

    # loop through the word-level ocr output and merge overlapping segments
    # if present in the line_merge mapping
    for i in range(len(word_level_ocr_output["words"])):
        if i not in line_merge_map and i not in follow_merge_map:
            linewise_ocr_output["full_line"].extend([word_level_ocr_output["words"][i]])

            linewise_ocr_output["bboxes"].extend([word_level_ocr_output["bboxes"][i]])

            linewise_ocr_output["page_id"].append(word_level_ocr_output["page_id"][i])

            linewise_ocr_output["ymin_min"].append(
                word_level_ocr_output["ymin_ymax"][i][0]
            )

            linewise_ocr_output["ymax_max"].append(
                word_level_ocr_output["ymin_ymax"][i][1]
            )

        else:
            if i in line_merge_map:
                line = []
                ymin_min = []
                ymax_max = []
                bboxes = []

                # if the index is present in the merge map then
                # iterate through the indices of word level entries
                # that are a part of that line and merge them
                for j in line_merge_map[i]:
                    line.extend(word_level_ocr_output["words"][j])
                    ymin_min.append(word_level_ocr_output["ymin_ymax"][j][0])
                    ymax_max.append(word_level_ocr_output["ymin_ymax"][j][1])
                    bboxes.extend(word_level_ocr_output["bboxes"][j])

                linewise_ocr_output["full_line"].append(line)
                linewise_ocr_output["bboxes"].append(bboxes)
                linewise_ocr_output["ymin_min"].append(ymin_min)
                linewise_ocr_output["ymax_max"].append(ymax_max)

                linewise_ocr_output["page_id"].append(
                    word_level_ocr_output["page_id"][i]
                )

    for idx, (min_element, max_element) in enumerate(
        zip(linewise_ocr_output["ymin_min"], linewise_ocr_output["ymax_max"])
    ):

        if isinstance(min_element, list):
            new_min_element = min(min_element)
            new_max_element = max(max_element)

            linewise_ocr_output["ymin_min"][idx] = new_min_element
            linewise_ocr_output["ymax_max"][idx] = new_max_element

    return linewise_ocr_output

import re
from thefuzz import fuzz

# TODO: Figure out logic to help out in debugging errors in matching


def get_toc_page_id(linewise_ocr_output):
    '''Returns the page_id of the table of contents page

    Args:
        linewise_ocr_output: dict. OCR results obtained after merging
            overlapping word-level segments into contiguous segments

    Returns:
        page_id: int. Page number of the table of contents page
    '''
    # define regex expression that we'll use to identify the table of contents
    regex_exp = r"(table of contents|tableof(?:contents)?|(?:table\s)?of*conten|contents?)"

    # loop through the linewise ocr output and try to find a match
    for page_id, line in zip(linewise_ocr_output['page_id'],
                             linewise_ocr_output['full_line']):

        # if the regex expression matches then return the page_id
        if re.search(regex_exp, " ".join(line).lower()):
            return page_id

    return None


def match_toc_label_with_ocr_seg(toc_label,
                                 linewise_ocr_output,
                                 idx1,
                                 idx2,
                                 subset_match_threshold,
                                 line_len_match_threshold,
                                 beg_line_match_threshold,
                                 first_line_match_threshold,
                                 toc_page_id):
    '''Matches the toc_labels from the parsed HTML with the OCR output

    Also accounts for cases where the toc_label spans multiple lines

    Args:
        toc_label: list. Single TOC section label for a given contract
        linewise_ocr_output: dict. Postprocessed OCR output
        idx1: int. Index of the first line
        idx2: int. Index of the second line
        subset_match_threshold: float.
        line_len_match_threshold: float.
        beg_line_match_threshold: float.
        first_line_match_threshold: float.
        toc_page_id: int. The page_id of the table of contents page

    Returns:


    '''
    # TODO: in first commented block- why is the first cond here, we check for toc_page earlier
    # TODO: second check is redundant since we also check if idx1 == idx2. If
    # TODO: we check the beg of the line and then check the first two words again why?
    # can't we just check the first two words directly?

    # if the current page is the toc_page then return without further
    # processing since we don't want to match with this page
    if linewise_ocr_output['page_id'][idx1] == toc_page_id:
        return None, None

    # idx1 == idx2 then we already checked if idx1 is the toc_page, so no need
    # to check if idx2 is toc_page again
    '''
    if (idx1 is not None) and (idx2 is not None):
        if linewise_ocr_output['page_id'][idx2] == toc_page:
            return None, None

        if linewise_ocr_output['page_id'][idx1] != linewise_ocr_output['page_id'][idx2]:
            return None, None

    '''

    if idx2 is not None:
        if (
                linewise_ocr_output['page_id'][idx1] !=
                linewise_ocr_output['page_id'][idx2]
           ):
            return None, None

        # merge text from the two lines
        multi_line_text = (linewise_ocr_output['full_line'][idx1] +
                           linewise_ocr_output['full_line'][idx2])
        multi_line_text = " ".join(multi_line_text)

        line1_text = " ".join(linewise_ocr_output['full_line'][idx1])

        # compute the fuzzy match score between the toc_label and
        # the given text_segment
        match_score = fuzz.partial_ratio(toc_label[0].lower(),
                                         multi_line_text.lower())

        # the match score must be greater than some min threshold
        full_text_match_cond = match_score >= subset_match_threshold

        # the matched text segment must have length at least some %-age of
        # the toc label it matched with
        match_len_cond = len(multi_line_text) >= (len(toc_label[0]) *
                                                  line_len_match_threshold)

        # since the toc label might be inline i.e. part of a longer text
        # segment, we also check if the beggining of the text segment
        # matches with the toc label

        # not really necessary for this case but keeping it for consistency
        beg_line_text = multi_line_text[0: len(toc_label[0]) * 2]

        # the beginning of the text segment must have some %-age of overlap
        # with the toc label
        beg_line_match_score = fuzz.partial_ratio(toc_label[0].lower(),
                                                  beg_line_text.lower())

        beg_line_match_cond = beg_line_match_score >= beg_line_match_threshold

        # for cases where the toc_label spans multiple lines, we check if
        # the first line of the text segment has some %-age of overlap
        # with the toc label
        first_line_match_score = fuzz.partial_ratio(toc_label[0].lower(),
                                                    line1_text.lower())

        first_line_match_cond = (first_line_match_score >=
                                 first_line_match_threshold)

        if (
            full_text_match_cond and match_len_cond and
            beg_line_match_cond and first_line_match_cond
           ):

            # check if the beginning of the toc_label
            # (first 2 words- design choice) has a high match with
            # the beginning of the matched line.
            toc_label_beg = toc_label[0].split()[:2]
            toc_label_beg = " ".join(toc_label_beg)

            matched_line_beg = multi_line_text.split()[:2]
            matched_line_beg = " ".join(matched_line_beg)

            first_2words_match_score = \
                fuzz.partial_ratio(toc_label_beg.lower(),
                                   matched_line_beg.lower())

            first_2words_match_cond = (first_2words_match_score >=
                                       subset_match_threshold)
            if first_2words_match_cond:

                # get y coord of top-left corner
                ymin = linewise_ocr_output['ymin_min'][idx1]

                # get y coord of bottom-right corner
                ymax = linewise_ocr_output['ymax_max'][idx2]

                page_id = linewise_ocr_output['page_id'][idx1]

                bboxes = [linewise_ocr_output['bboxes'][idx1],
                          linewise_ocr_output['bboxes'][idx2]]

                line2_text = " ".join(linewise_ocr_output['full_line'][idx2])

                return (line1_text,
                        line2_text,
                        toc_label[0],
                        ymin,
                        ymax,
                        page_id,
                        bboxes), idx2 + 1

            # if the beginning of the toc label and the matched line
            # don't have a high match then return None
            else:
                return None, None

        # if the match cond in the if statement fail, then return None
        return None, None

    # get the text of the line
    line_text = " ".join(linewise_ocr_output['full_line'][idx1])

    # compute the fuzzy match score between the toc_label and
    # the given text_segment
    match_score = fuzz.partial_ratio(toc_label[0].lower(),
                                     line_text.lower())

    # the match score must be greater than some min threshold
    full_text_match_cond = match_score >= subset_match_threshold

    # the matched text segment must have length at least some %-age of
    # the toc label it matched with
    match_len_cond = len(line_text) >= (len(toc_label[0]) *
                                        line_len_match_threshold)

    # since the toc label might be inline i.e. part of a longer text
    # segment, we also check if the beggining of the text segment
    # matches with the toc label

    # index out of the beginning of the line
    beg_line_text = line_text[0: len(toc_label[0]) * 2]

    # the beginning of the text segment must have some %-age of overlap
    # with the toc label
    beg_line_match_score = fuzz.partial_ratio(toc_label[0].lower(),
                                              beg_line_text.lower())

    beg_line_match_cond = beg_line_match_score >= beg_line_match_threshold

    if (full_text_match_cond and match_len_cond and beg_line_match_cond):

        # check if the beginning of the toc_label
        # (first 2 words- design choice) has a high match with
        # the beginning of the matched line.
        toc_label_beg = toc_label[0].split()[:2]
        toc_label_beg = " ".join(toc_label_beg)

        matched_line_beg = line_text.split()[:2]
        matched_line_beg = " ".join(matched_line_beg)

        first_2words_match_score = fuzz.partial_ratio(toc_label_beg.lower(),
                                                      matched_line_beg.lower())

        first_2words_match_cond = (first_2words_match_score >=
                                   subset_match_threshold)

        if first_2words_match_cond:
            # get y coord of top-left corner
            ymin = linewise_ocr_output['ymin_min'][idx1]

            # get y coord of bottom-right corner
            ymax = linewise_ocr_output['ymax_max'][idx1]

            page_id = linewise_ocr_output['page_id'][idx1]

            bboxes = linewise_ocr_output['bboxes'][idx1]

            return (line_text,
                    None,
                    toc_label[0],
                    ymin,
                    ymax,
                    page_id,
                    bboxes), idx1 + 1

        # if the beginning of the toc label and the matched line
        # don't have a high match then return None
        else:
            return None, None

    # if the match cond in the if statement fail, then return None
    return None, None


def find_single_match_id(toc_label,
                         linewise_ocr_output,
                         subset_match_threshold,
                         line_len_match_threshold,
                         beg_line_match_threshold,
                         first_line_match_threshold,
                         prev_line_pointer):
    '''Finds the index of the OCR segment with the highest match score with
        a given toc label

    Given a toc section label, iterate all the lines in the file
    from the last line associated with a section title

    Args:
        toc_label: list. Single TOC section label for a given contract
        linewise_ocr_output: dict. Postprocessed OCR output
        subset_match_threshold: float.
        line_len_match_threshold: float.
        beg_line_match_threshold: float.
        first_line_match_threshold: float.
        prev_line_pointer: int. The index of the last line matched with a
            toc section label

    Returns:
        match_info: tuple. Contains metadata associated with the matched
            segment such as the matched text, ymin, ymax, page_id and coords
            of the bbox
        prev_line_pointer: int. The index of the last line matched with a
            toc section label
    '''

    if prev_line_pointer == len(linewise_ocr_output['full_line']):
        return None, prev_line_pointer

    # get the page id of the table of contents page
    toc_page_id = get_toc_page_id(linewise_ocr_output)

    itertuple = zip(
                        range(prev_line_pointer,
                              len(linewise_ocr_output['full_line'])),
                        range(prev_line_pointer + 1,
                              len(linewise_ocr_output['full_line']))
                    )

    for idx1, idx2 in itertuple:

        # first try matching with first line
        match_info, updated_prev_line_pointer = \
            match_toc_label_with_ocr_seg(toc_label,
                                         linewise_ocr_output,
                                         idx1,
                                         None,
                                         subset_match_threshold,
                                         line_len_match_threshold,
                                         beg_line_match_threshold,
                                         first_line_match_threshold,
                                         toc_page_id)
        if match_info:
            return match_info, updated_prev_line_pointer

        # let's try matching with second line only
        match_info, updated_prev_line_pointer = \
            match_toc_label_with_ocr_seg(toc_label,
                                         linewise_ocr_output,
                                         idx2,
                                         None,
                                         subset_match_threshold,
                                         line_len_match_threshold,
                                         beg_line_match_threshold,
                                         first_line_match_threshold,
                                         toc_page_id)
        if match_info:
            return match_info, updated_prev_line_pointer

        # now try matching with 2 lines
        match_info, updated_prev_line_pointer = \
            match_toc_label_with_ocr_seg(toc_label,
                                         linewise_ocr_output,
                                         idx1,
                                         idx2,
                                         subset_match_threshold,
                                         line_len_match_threshold,
                                         beg_line_match_threshold,
                                         first_line_match_threshold,
                                         toc_page_id)

        if match_info:
            return match_info, updated_prev_line_pointer

        # if no match, move onto the next pair of lines
        continue

    return None, prev_line_pointer


def find_all_match_ids(toc_match_config,
                       toc_label_dict,
                       linewise_ocr_output):
    '''Finds the index of the OCR segment with the highest match score with
        a given toc label for all toc labels in a single contract

    Args:
        toc_match_config: dict. Contains all user-defined params
            for executing the matching pipeline
        toc_label_dict: dict. Mapping of all section labels for a given
            contract
        linewise_ocr_output: dict. Postprocessed OCR output

    Returns:
        all_match_info: tuple. Contains metadata associated with the matched
            segment such as the matched text, ymin, ymax, page_id and coords
            of the bbox for all section labels for a single contract
    '''

    # Design decision to only allow subset match ratios of >= 80/100
    subset_match_threshold = toc_match_config['subset_match_threshold']

    # Design decision to potentially only match document lines
    # that are at least as long as some percentage of the toc label
    line_len_match_threshold = toc_match_config['line_len_match_threshold']

    # Design decision to ensure that the beginning of the matched lines
    # have match ratios of >= 80/100
    beg_line_match_threshold = toc_match_config['beg_line_match_threshold']

    # in case of toc labels that span multiple lines
    # ensure the top line is at least mildly relevant
    first_line_match_threshold = toc_match_config['first_line_match_threshold']

    all_match_info = []
    prev_line_pointer = 0  # init the pointer to the first line
    for _, toc_label in toc_label_dict.items():
        match_info, prev_line_pointer = \
            find_single_match_id(toc_label,
                                 linewise_ocr_output,
                                 subset_match_threshold,
                                 line_len_match_threshold,
                                 beg_line_match_threshold,
                                 first_line_match_threshold,
                                 prev_line_pointer)
        if match_info:
            all_match_info.append(match_info)

        else:
            print(f"Couldn't match {toc_label[0]} with a line." +
                  "Moving onto next TOC section")

    return all_match_info

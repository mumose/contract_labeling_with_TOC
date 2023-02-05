from thefuzz import fuzz
from thefuzz import process


def merge_bboxes(
    line1_words, line2_words, toc_label, bboxes, num_words_toc_label, match_score_toc
):
    """Extracts the bboxes of the subset of the matched text segment that
    matches closest to the toc label.

    We iterate through windows of text in the matched text to try and determine
    the text segment that matches closest with the toc label. The size of the
    window is equal to the num of words in the toc label.

    For each window, we compare its fuzzy match score with the toc label and
    select the window that has the highest fuzzy match score

    Args:
        line1_words: str. Text contained in the first line of the
            matched text segment from OCR
        line2_words: str. Text contained in the second line of the
            matched text segment from OCR
        toc_label: str. Text contained in the matched section label
        bboxes: List[List[int]]: The bounding box coordinates of each word in
            the matched text segment from OCR
        num_words_toc_label: int. Number of words in the toc label.
            We need to index out these many bbox entries from the matched text
        match_score_toc: float. The fuzzy match score for the full line of
            text and the toc label.

    Returns:

    """
    # split the str into a list of words and then combine the words
    # for the two lines
    if isinstance(line1_words, str):
        line1_words = line1_words.split()

    if isinstance(line2_words, str):
        line2_words = line2_words.split()

    if line2_words:
        full_line_words = line1_words + line2_words
    else:
        full_line_words = line1_words

    # keep track of the highest matched score
    max_window_score = 0

    # we iterate over non-overlapping windows of the list of words in the
    # text segment
    for _, start_idx in enumerate(range(0, len(full_line_words), num_words_toc_label)):

        window_text = " ".join(
            full_line_words[start_idx : (start_idx + num_words_toc_label)]
        )

        window_match_score = process.extractBests(
            window_text, [toc_label], scorer=fuzz.token_set_ratio
        )[0][-1]

        # if a second line exists then we keep track of all the bboxes so we
        # can that the final bbox can be obtained by merging the
        # bboxes across lines. In case only a single line is present then we
        # obtain the bboxes for just the window we're currently looking at
        if line2_words:
            candidate_bboxes = bboxes[0] + bboxes[1]
        else:
            candidate_bboxes = bboxes[start_idx : (start_idx + num_words_toc_label)]

        # if the fuzzy match score of the window is greater than the
        # match score of the full line with the toc then find the
        # final bbox coords and return
        if window_match_score >= match_score_toc:
            # x min is the x_left of the first bbox
            # y_min is the min of the top left y's for each box
            x_min = min([x[0][0] for x in candidate_bboxes])
            y_min = min([y[0][-1] for y in candidate_bboxes])

            # x max is the x_right of the last bbox
            # y_max is the max of the bottom_right y's for each box
            x_max = max([x[1][0] for x in candidate_bboxes])
            y_max = max([y[1][-1] for y in candidate_bboxes])

            merged_bbox = [[x_min, y_min], [x_max, y_max]]

            return merged_bbox, window_text

        else:
            # if the fuzzy match score of the window is greater than the
            # current highest match score then keep track of the score, the
            # matched text and it's bboxes
            if window_match_score > max_window_score:
                max_window_score = window_match_score
                match_text = window_text
                match_candidate_bboxes = candidate_bboxes

            continue

    # in case the window_text has a lower match score than with the
    # entire string, match with the segment with highest matching score
    x_min = min([x[0][0] for x in match_candidate_bboxes])
    y_min = min([y[0][-1] for y in match_candidate_bboxes])

    # x max is the x_right of the last bbox
    # y_max is the max of the bottom_right y's for each box
    x_max = max([x[1][0] for x in match_candidate_bboxes])
    y_max = max([y[1][-1] for y in match_candidate_bboxes])

    merged_bbox = [[x_min, y_min], [x_max, y_max]]

    return merged_bbox, match_text


def extract_exact_match(row):
    """Extracts the bbox and text segment that matches exactly with
       the toc label

    The matched line from OCR may contain superfluous text in cases where the
    section label is part of a larger text segment in the contract. In such
    cases, we want to extract the bbox coords and text that corresponds to
    just the section label and ignore the rest of the text segment

    Args:
        row: pd.Series. Row from the metadata df that is obtained after
            toc matching. It must contain the following cols
                - Section Title via HTML
                - Line1 via OCR
                - Line2 via OCR
                - bboxes

    Returns:
        merged_bbox: List[List[int]]. The bbox coords corresponding to the
            text segment that matched most closely with the toc label
        exact_match_text: str. Text of the segment that matched
            most closely with the toc label
    """
    toc_label = row["Section Title via HTML"]
    bboxes = row["bboxes"]
    if toc_label is not None:
        line1_text = row.loc["Line1 via OCR"]
        line2_text = row.loc["Line2 via OCR"]

        if line2_text is not None:
            full_line_text = line1_text + line2_text
        else:
            full_line_text = line1_text

        # get the match score of the full text segment with the toc label
        # it will help us identify if the full line contains superfluous
        # text in which case we will be able to find a window within the
        # full text that returns a higher fuzzy matche score with
        # the toc label
        match_toc = process.extractBests(
            full_line_text, [toc_label], scorer=fuzz.token_set_ratio
        )

        # match_text_toc is the text in the best matching
        # toc label
        match_text_toc, match_score_toc = match_toc[0]
        num_words_toc_label = len(match_text_toc.split())

        merged_bbox, exact_match_text = merge_bboxes(
            line1_text,
            line2_text,
            toc_label,
            bboxes,
            num_words_toc_label,
            match_score_toc,
        )

        return merged_bbox, exact_match_text

    else:
        return None, None

# For a single toc extraction, output a file in a specified output folder
import roman
import re, statistics


def extract_td(cell):
    """Extracts the data tag

    Args:
        cell: b24 cell. has the cell information within the TD

    Returns:
        text: str. the cleaned text within the cell
    """
    text = ""
    if cell.p:
        text = cell.p.text
    if cell.text:
        text = cell.text
    text = re.sub(r"[^\x00-\x7f]", r"", text)
    text = text.replace("\n", " ")
    return text.strip()


def clean(table_list):
    """Cleans the results of table parsing

    Args:
        table_list: list. list containing the results of parsing the TOC

    Returns:
        table_list: list. list containing the rows with enough columns
    """
    try:
        num_cols = statistics.mode([len(x) for x in table_list])
    except statistics.StatisticsError as e:
        print("Multi mode, skipping")
        return table_list
    table_list = [x for x in table_list if len(x) == num_cols]
    return table_list


def parse_html(soup):
    """Parses the html

    Args:
        soup: bs4 object. the bs4 representation of the html file

    Returns:
        table_holder: list. contains the values from the table
    """
    table_holder = []
    for table in soup.find_all("table"):
        for row in table.tbody.find_all("tr"):
            row_holder = []
            for cell in row.find_all("td"):
                text = extract_td(cell)
                if text:
                    row_holder.append(text)
            if row_holder:
                table_holder.append(row_holder)
    if table_holder:
        table_holder = clean(table_holder)
    return table_holder


def filter_contents(s):
    """Prepares the data by finding the start of the table

    Args:
        master_df: str. the string representation of the html file

    Returns:
        remaining: str. the string from when the first table tag begins
    """
    multi_page_join_distance = 5000
    cont = re.split("table of contents", s, flags=re.IGNORECASE)
    if len(cont) == 1:
        cont = re.split("contents", s, flags=re.IGNORECASE)
    remaining = "".join(cont[1:])
    ind_start = remaining.find("<table")
    remaining = remaining[ind_start:]

    indices = [
        m.start() for m in re.finditer("</table>", remaining, flags=re.IGNORECASE)
    ]
    valid_index = [x for x in indices if x < multi_page_join_distance]
    if valid_index:
        print("Combining table on next page")
        return remaining[: valid_index[-1] + 10]
    return remaining[:multi_page_join_distance]


def refine_table(toc):
    """
    Parameters
    ----------
    toc_extracted: list of [str, dict]
      The toc which has been processed to extract each line of the toc.
      This list contains the actual extracted dict as well as the contract title.
    """

    label_dict = {}
    n_section = 1
    n_subsection = 1

    ### Roman Numeral Check
    roman_numerals = ["II", "III", "IV", "VII", "VIII", "IX", "XI", "XII"]
    numeral_counter = 0
    is_roman = False

    for item in toc:
        if numeral_counter >= 2:
            is_roman = True
            break
        is_subsection = re.search("\d\.(\d)+", item[0])
        if not is_subsection:
            if any(romans in item[0] for romans in roman_numerals):
                numeral_counter += 1

    ### Label Extraction
    for item in toc:

        # Section number regex rules to handle improperly ordered inputs
        if re.search("\.(\d\d) \n\d", item[0]):
            item[0] = item[0][-2:] + item[0][1:3]
        if re.search("\.(\d\d)(\n)+\d", item[0]):
            item[0] = item[0][-2:] + item[0][1:3]
        if re.search("\.(\d)+ [\D]+ \d\.", item[0]):
            item[0] = item[0][-2:] + item[0][1:-2]

        # Determine if line is a subsection using regex
        is_subsection = re.search("(\d)+\.(\d)+", item[0])
        # print(item)
        if re.search("\d\.0", item[0]):
            is_subsection = False

        if not is_subsection:
            n_section_str = roman.toRoman(n_section) if is_roman else f"{n_section}"

            if n_section_str in item[0]:
                section_title = item[0]

                if len(item) > 1:
                    try:
                        int(item[1])
                    except:
                        section_title = f"{section_title} {item[1]}"

                label_dict[n_section] = (section_title, {})
                n_section += 1
                n_subsection = 1

        else:
            # Is a section title with d.d style numbering
            # print(item)
            if len(item) == 2:
                section_title = " ".join(re.split("(\d\.\d+)", item[0])).strip()
                label_dict[n_section] = (section_title + " " + item[1], {})
                n_section += 1
            # Is an actual subsection
            else:
                # print(n_section, n_subsection, is_subsection.group(), item, contract_title)
                concat_items = " ".join(item[1:])
                try:
                    label_dict[n_section - 1]
                except:
                    label_dict[n_section - 1] = ("Miscellanous Subsections", {})

                label_dict[n_section - 1][1][n_subsection] = (
                    f"{is_subsection.group()} {concat_items}",
                    {},
                )

            n_subsection += 1

    return label_dict

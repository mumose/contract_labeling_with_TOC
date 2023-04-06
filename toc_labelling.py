# For a single toc extraction, output a file in a specified output folder
import re
import roman
from pprint import pprint
import json
import os



def extract_label_to_json(toc_extracted, output_dir):
  '''
  Parameters
  ----------
  toc_extracted: list of [str, dict]
    The toc which has been processed to extract each line of the toc. 
    This list contains the actual extracted dict as well as the contract title.

  output_dir: str
    Directory where the new json file will be created.
  '''
    

  contract_title = toc_extracted[0]
  toc = toc_extracted[1]

  label_dict = {}
  n_section = 1
  n_subsection = 1

  ### Roman Numeral Check
  roman_numerals = ['II', 'III', 'IV', 'VII', 'VIII', 'IX', 'XI', 'XII']
  numeral_counter = 0
  is_roman = False

  for item in toc:
    if numeral_counter >= 2:
      is_roman = True
      break
    is_subsection = re.search('\d\.(\d)+', item[0])
    if not is_subsection:
      if any(romans in item[0] for romans in roman_numerals):
        numeral_counter += 1

  ### Label Extraction
  for item in toc:

    # Section number regex rules to handle improperly ordered inputs
    if re.search('\.(\d\d) \n\d', item[0]):
      item[0] = item[0][-2:] + item[0][1:3]
    if re.search('\.(\d\d)(\n)+\d', item[0]):
      item[0] = item[0][-2:] + item[0][1:3]
    if re.search('\.(\d)+ [\D]+ \d\.', item[0]):
      item[0] = item[0][-2:] + item[0][1:-2]
    
    # Determine if line is a subsection using regex
    is_subsection = re.search('(\d)+\.(\d)+', item[0])
    # print(item)
    if re.search('\d\.0', item[0]):
      is_subsection = False

    if not is_subsection:
      n_section_str = roman.toRoman(n_section) if is_roman else f'{n_section}'

      if n_section_str in item[0]:
        section_title = item[0]

        if len(item) > 1:
          try:
            int(item[1]) 
          except:
            section_title = f'{section_title} {item[1]}'
        
        label_dict[n_section] = (section_title, {})
        n_section += 1
        n_subsection = 1

    else:
      # Is a section title with d.d style numbering
      # print(item)
      if len(item) == 2:
        section_title = ' '.join(re.split('(\d\.\d+)', item[0])).strip() 
        label_dict[n_section] = (section_title + ' ' + item[1], {})
        n_section += 1
      # Is an actual subsection
      else:
        # print(n_section, n_subsection, is_subsection.group(), item, contract_title)
        concat_items = ' '.join(item[1:])
        label_dict[n_section-1][1][n_subsection] = (f'{is_subsection.group()} {concat_items}', {})
        
      n_subsection += 1

  labels_title = '/' + contract_title[:contract_title.find('_')]
  with open(output_dir + labels_title, 'w') as f:
    json.dump(label_dict, f)

  return contract_title, label_dict

def extract_labels_to_folder(dict_of_tocs, output_dir, contract_map):
  '''
  Outputs both a folder of json outputs for each contract along with a single json containing
  all outputs in a dictionary format.

  Parameters
  ----------
  dict of tocs: dict of str:list
    The toc which has been processed to extract each line of the toc. 
    This list contains the actual extracted dict as well as the contract title.

  output_dir: str
    Directory where the new json files will be pushed to. 
    If the directory does not exist it will be created.
  '''
  agg_label_dict = {}
  id_map = {v:k for k, v in contract_map.items()}

  for item in dict_of_tocs.items():
    print(item[0])
    if item[0] in agg_label_dict.keys():
      continue
    if 'Monsanto Company' in item[0]:
      continue
    if not os.path.isdir(output_dir):
      os.makedirs(output_dir)
    out = extract_label_to_json(item, output_dir)
    id = id_map[out[0][:-5]]
    agg_label_dict[id] = out[1]

  with open('./TOC_Labels_full.json', 'w') as f:
    json.dump(agg_label_dict, f)




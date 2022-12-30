import json
from toc_labelling import extract_label_to_json, extract_labels_to_folder

with open('/Users/rohith/Downloads/scraping_results_full.json', 'r') as f:
  scraping_results = json.load(f)

with open('contract_name_map.json', 'r') as f:
  contract_map = json.load(f)


id_map = {v:k for k, v in contract_map.items()}
for k, v in scraping_results.items():
  if 'Monsanto Company' in k:
    continue 
  print(id_map[k[:-5]])

# with open('/Users/rohith/Downloads/labelling_results_sample.json', 'r') as f:
#   sample = json.load(f)

imp_dict = extract_labels_to_folder(scraping_results, 'labelled_outputs_full', contract_map)

# out = {}
# for k, v in sample.items():
#   out[id_map[k[:-5]]] = v

# with open('/Users/rohith/Downloads/labelling_results_mapped_sample.json', 'w') as f:
#   json.dump(out, f)
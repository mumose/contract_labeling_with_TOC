from transformers import MarkupLMFeatureExtractor
from transformers import AutoProcessor, AutoModelForSequenceClassification
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using device:', device)

feature_extractor = MarkupLMFeatureExtractor()
# with open('./glacier_altabancorp.html') as f:
# with open('./open_zix.html') as f:
# with open('./california_pacific.html') as f:
# with open('./alaska_project8.htm') as f:
# with open('./ready_anworth.htm') as f:
with open('./delta_alexion.htm') as f:
  html_code = f.read()
encoding = feature_extractor(html_code)

processor = AutoProcessor.from_pretrained("microsoft/markuplm-base", truncation=True)
model = AutoModelForSequenceClassification.from_pretrained("microsoft/markuplm-base", num_labels=4).to(device)
processor.parse_html = False

start_node_idx = 0
end_node_idx = 400

nodes = encoding['nodes'][0][start_node_idx:end_node_idx]
xpaths = encoding['xpaths'][0][start_node_idx:end_node_idx]
important_nodes = []
possible_text_starts = ['TABLE OF CONTENTS', 'TOC', 'TABLE OF CONTENT']
possible_text_ends = ['AGREEMENT AND PLAN OF MERGER', 'PLAN AND AGREEMENT OF MERGER', 'AGREEMENT AND PLAN OF REORGANIZATION']
possible_xpath_starts = ['table', 'table[1]', 'table[2]', 'table[3]'] # Modify code to allow for any number of tables before end value
possible_xpath_ends = []
text_types = ['section_title', 'paragraph', 'table', 'other']

def table_in_xpath(xpath):
   S1, S2 = set(possible_xpath_starts), set(xpath)
   return len(S1.intersection(S2)) > 0


print("###################################################")
started = False
ended = False
xpath_lists = [path.split('/')[-7:] for path in xpaths]
start: "list[int, str]" = [0, '', '']
end: "list[int, str]" = [0, '', '']
section_titles = []
for i in range(len(xpath_lists)):
  text = nodes[i].strip()
  xpath_list = xpath_lists[i]
  xpath_str = xpaths[i]

  if not started:
    if (text in possible_text_starts) or table_in_xpath(xpath_list): 
        print(i)
        print('Possible START: ', text, xpath_list)
        started = True
        start = [i, text, xpath_list]

  elif started and not ended:

    if 'table' in xpath_list:
        print(nodes[i], xpath_lists[i])
    if (text in possible_text_ends):
        print(i)
        print('Possible END: ', text, xpath_list)
        ended = True
        end = [i, text, xpath_list]

   
print("###################################################")


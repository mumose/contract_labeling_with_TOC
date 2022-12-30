import json
import glob

root_dir = '/Users/rohith/Documents/CUAD_v1/full_contract_pdf/'

# root_dir needs a trailing slash (i.e. /root/dir/)
num_files = 0
contract_name_list = []

for filename in glob.iglob(root_dir + '**/*.pdf', recursive=True):
    filename_list = filename.split('/')[6:]
    contract_name_list.append(filename_list)
    num_files += 1
for filename in glob.iglob(root_dir + '**/*.PDF', recursive=True):
    filename_list = filename.split('/')[6:]
    contract_name_list.append(filename_list)
    num_files += 1

contract_name_list.sort(key=lambda x:x[2])

contract_full_map = {}
id_counter = 0
for contract in contract_name_list: 
    contract_full_map[f'ct_{id_counter}'] = {'part': contract[0], 'type': contract[1], 'id':contract[2][:-4]} 
    id_counter += 1

contract_name_map = {}
id_counter = 0
for contract in contract_name_list: 
    contract_name_map[f'ct_{id_counter}'] = contract[2][:-4]
    id_counter += 1

with open('contract_full_map.json', 'w') as f1:
    json.dump(contract_full_map, f1)
with open('contract_name_map.json', 'w') as f2:
    json.dump(contract_name_map, f2)
print(contract_name_map)
print(num_files)
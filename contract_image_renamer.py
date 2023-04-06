import json
import glob
import os

root_dir = '/Users/rohith/Downloads/cuad_imgs_labeled'


# # RENAME ALL CONTRACT IMAGES IN ROOT DIR

# for _, folder in enumerate(os.listdir(root_dir)):
#     if folder == '.DS_Store':
#         continue
#     for count, file in enumerate(os.listdir(f"{root_dir}/{folder}")):
#         if file == '.DS_Store':
#             continue
#         new_fname = folder + "_" + file[-6:]
#         print(new_fname)
#         os.rename(f"{root_dir}/{folder}/{file}", f"{root_dir}/{new_fname}")

# GET ALL IMAGE NAMES INTO JSON
page_nums_dict = {}
for count, filename in enumerate(os.listdir(root_dir)):
        if filename == '.DS_Store':
            continue
        ct_id = filename[:6]
        file_no = filename[7:9]
        try:
            page_nums_dict[ct_id].append(file_no)
            
        except:
            page_nums_dict[ct_id] = []

for k, v in page_nums_dict.items():
    page_nums_dict[k] = sorted(v)      
print(page_nums_dict)
   

unlabeled_dir = '/Users/rohith/Downloads/cuad_images_labeled_s'
for _, folder in enumerate(os.listdir(unlabeled_dir)):
    if folder == '.DS_Store':
        continue
    print(folder)
    for count, file in enumerate(os.listdir(f"{unlabeled_dir}/{folder}")):
        if file == '.DS_Store':
            continue
        print(int(file[-6:-4]))
        if file[-6:-4] in page_nums_dict[folder]:
            print(file[-6:-4])
            new_fname = folder + "_" + file[-6:]
        # print(new_fname)
        # print(f"{unlabeled_dir}/{folder}/{file}", f"{unlabeled_dir}/{new_fname}")
            os.rename(f"{unlabeled_dir}/{folder}/{file}", f"{unlabeled_dir}/{new_fname}")

# for k, v in page_nums_dict.items():
#     page_nums_dict[k] = sorted(v)    
# with open('ct_id_valid_page_numbers.json', 'w') as f:
#     json.dump(page_nums_dict, f)


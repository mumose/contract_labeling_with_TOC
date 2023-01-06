# contract_labeling_with_TOC
* We’ve saved the json output for **ALL** the contracts in a single JSON file. 
* Each key in this JSON is of the form ct_x and its corresponding value contains the pipeline output for a single contract. 
* Each of these (contract level output) in turn consists of the following keys:
  * ***pages***- 
    * a list of dicts that contains page level information for the contract. It consists of the following information:
      * ***dimensions***- 
        * the dimensions for that page of the contract in the form (width, height) in pixels
        * dtype: Tuple(int, int)
        * Eg: (1653, 2339)
      * ***bbox***-
        * A list of dicts containing bounding box level information. Each dict includes the following key-value pairs:
          * ***corr***:  
            * contains the coordinates of for that bounding box in the form ((x1, y1), (x2, y2)), specifying the upper left and lower right corners of the bounding box
            * dtype: List[List[int]]
            * Eg: [[221, 1190], [699, 1232]]
          * ***text_via_ocr***-
            * The predicted text extracted from our pipeline 
            * dtype: str
            * Eg: “ARTICLE2. GRANTOF RIGHTS"
          * ***text_via_html***-
            * The ground truth text extracted from parsing the HTML of the contract
            * dtype: str
            * Eg: "Article 2. Grant of Rights"
        * **If no section label is found on a page, then the bbox value for that page will be NULL**
      * ***path_to_image***-
        * The path to the raw image of that page (without bounding box outputs drawn on it)
        * dtype: str
        * Eg: cuad_pipeline_output/ct_506/raw_images/69a9eabe-3c93-4340-839a-3ff3566ed205-01.jpg
      * ***path_to_image_with_bounding_box***-
        * The path to the predicted image of that page, with bounding boxes drawn on it. 
        * dtype: str
        * Eg: cuad_pipeline_output/ct_506/images_with_bounding_boxes/ccf97929-1f78-4fad-99ac-6fd20ae799b8-06.jpg
        * **If no section label is found on a page, then this value for that page will be NULL**
      * ***path_to_pdf***-
        * The path to the PDF version of the contract
        * dtype: str
        * Eg: cuad_pipeline_output/ct_506/contract_pdf/ct_506.pdf
      * ***path_to_html***-
        * The path to the HTML version of the contract
        * dtype: str
        * Eg: cuad_pipeline_output/ct_506/contract_html/ct_506.htm
* The zip file consists of the following structure
  * sample_for_website
    * cuad_pipeline_output
      * ct_x
        * images_with_bounding_boxes
          * image1.jpg
          * image2.jpg
        * raw_images
          * image1.jpg
          * image2.jpg
        * contract_pdf
          * ct_x.pdf
        * contract_html
          * ct_x.htm
    * dictionary_and_image_data.json
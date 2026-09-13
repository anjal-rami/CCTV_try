# Edge LPR

A high performance LPR pipeline utilizing Yolov8n for license plate detection and PaddleOCR for reading license plates  

### Dataset and Usage
The dataset is a demo of a parking lot use case and the Yolov8 model was trained on this. Usage of this dataset is restricted to smart parking license plate recognition applications and not for other unrelated surveillance tasks. 

### DL Streamer Integration
The pipeline has been tested and ran within Intel DL Streamer. Please follow the setup instructions provided by Deep Learning Streamer and you can use the pipeline command shown below as an example to run the pipeline and save the output annotated frame
```
gst-launch-1.0 filesrc location=ParkingVideoTrimmed2.mp4 ! decodebin3 ! vapostproc ! video/x-raw\(memory:VAMemory\) ! queue ! gvadetect model=yolov8n/yolov8n_retrained.xml device=GPU pre-process-backend=va-surface-sharing ! queue ! videoconvert ! gvaclassify model=mock_directory_setup/ch_PP-OCRv4_rec_infer/ch_PP-OCRv4_rec_infer.xml device=CPU pre-process-backend=opencv ! queue ! gvawatermark ! gvafpscounter ! vah264enc ! h264parse ! mp4mux ! filesink location=yolov8_lpr_output_toll_booth.mp4
```


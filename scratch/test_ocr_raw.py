import cv2  # type: ignore # pyrefly: ignore [missing-import]
import numpy as np  # type: ignore # pyrefly: ignore [missing-import]
import openvino as ov  # type: ignore # pyrefly: ignore [missing-import]

core = ov.Core()
model = core.read_model('app/services/lpr/models/ch_PP-OCRv4_rec_infer.xml')
compiled = core.compile_model(model, 'CPU')

with open('app/services/lpr/models/ppocr_keys_v1.txt', 'r', encoding='utf-8') as f:
    char_list = [line.strip('\r\n') for line in f]

# Index 0 is blank, 1 to 6623 is char_list, 6624 is space
char_dict = {i+1: char_list[i] for i in range(len(char_list))}
char_dict[0] = '' # blank
char_dict[len(char_list) + 1] = ' ' # space

img = cv2.imread('app/services/lpr/samples/sample_frame.jpg')
assert img is not None, "Failed to load sample image"
# Crop detected plate
x1, y1, x2, y2 = 976, 453, 1022, 469
margin = 4
x1_m = max(0, x1 - margin)
y1_m = max(0, y1 - margin)
x2_m = min(img.shape[1], x2 + margin)
y2_m = min(img.shape[0], y2 + margin)
crop = img[y1_m:y2_m, x1_m:x2_m]

crop_h, crop_w = crop.shape[:2]
target_h = 48
target_w = 192

r = target_h / crop_h
new_w = min(int(round(crop_w * r)), target_w)
resized_crop = cv2.resize(crop, (new_w, target_h))
padded_crop = np.zeros((target_h, target_w, 3), dtype=np.uint8)
padded_crop[:, :new_w] = resized_crop

blob = cv2.cvtColor(padded_crop, cv2.COLOR_BGR2RGB)
blob = (blob.astype(np.float32) / 255.0 - 0.5) / 0.5
blob = blob.transpose(2, 0, 1)[np.newaxis, ...]

output = compiled([blob])[compiled.output(0)]
preds = output[0] # [24, 6625]
pred_indices = np.argmax(preds, axis=1)

# Softmax
exp_preds = np.exp(preds - np.max(preds, axis=1, keepdims=True))
probs = exp_preds / np.sum(exp_preds, axis=1, keepdims=True)
confidences = np.max(probs, axis=1)

decoded_chars = []
char_confs = []
prev_idx = 0
for t, (idx, c) in enumerate(zip(pred_indices, confidences)):
    if idx != 0 and idx != prev_idx:
        decoded_chars.append(char_dict.get(idx, ''))
        char_confs.append(float(probs[t, idx]))
    prev_idx = idx

plate_text = ''.join(decoded_chars)
avg_conf = float(np.mean(char_confs)) if char_confs else 0.0
print(f'RECOGNIZED PLATE TEXT: "{plate_text}", confidence={avg_conf:.3f}')

import argparse
import subprocess
import os
import cv2
import random
import csv
import yaml
import numpy as np
from ultralytics import YOLO
from plot_result.plot import plot_one_box_only_pil
from PIL import Image

def load_config(path, model_name):
    with open(path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config.get(model_name, {})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Stream Processing with YOLO")
    parser.add_argument("--input_stream", type=str, default="rtmp://localhost:1935/obs/stream", 
                        help="RTMP input stream URL")
    parser.add_argument("--output_stream", type=str, default="rtmp://localhost:1935/output/stream", 
                        help="RTMP output stream URL")
    parser.add_argument("--ffmpeg_path", type=str, default=r"D:/VideoStream/ffmpeg/bin/ffmpeg.exe",
                        help="Path to the ffmpeg executable")
    parser.add_argument("--yolo_model_path", type=str, default="yolo-train/train/weights/best.pt",
                        help="Path to the YOLO model weights")
    parser.add_argument("--write_csv", type=bool, default=True,
                        help="Whether to write detection results to CSV")
    parser.add_argument("--csv_path", type=str, default="output.csv",
                        help="Path to save the CSV file")
    parser.add_argument("--model_name", type=str, default="construction_detect_construction_mengft-v1.0.20250402",
                        help="model name in config/plot_name_ch.yml")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.input_stream)
    fps = cap.get(cv2.CAP_PROP_FPS)
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    sizeStr = f"{size[0]}x{size[1]}"

    # 检查 ffmpeg_path 是否存在
    if not os.path.isfile(args.ffmpeg_path):
        print(f"Warning: Specified ffmpeg_path '{args.ffmpeg_path}' not found. Using 'ffmpeg' instead.")
        ffmpeg_path = 'ffmpeg'

    command = [
        ffmpeg_path, '-y', '-an', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', sizeStr, '-r', str(fps), '-i', '-', '-tune', 'zerolatency', '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p', '-preset', 'ultrafast', '-f', 'flv', args.output_stream
    ]
    pipe = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE)

    mapping_ch = load_config(path="config/plot_name_ch.yml", model_name=args.model_name)
    
    model = YOLO(args.yolo_model_path)
    names = model.model.names
    colors = {label: [random.randint(0, 255) for _ in range(3)] for label in set(names.values())}

    frame_count = 0
    csv_file = None
    csv_writer = None
    
    if args.write_csv:
        csv_file = open(args.csv_path, mode='w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Timestamp", "Class", "Coordinates", "Confidence"])
    
    while True:
        ret, im0 = cap.read()
        if not ret:
            print("Video processing completed or stream ended.")
            break
        if frame_count == 0:
            print("<-----------------------model loads successfully and prepares to detect!---------------------->")
        frame_count += 1
        hours = int(frame_count / (fps * 3600))
        minutes = int((frame_count % (fps * 3600)) / (fps * 60))
        seconds = int((frame_count % (fps * 60)) / fps)
        frames = int(frame_count % fps)
        timestamp = f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

        results = model.predict(im0)
        confs, boxes, cls_num = results[0].boxes.conf, results[0].boxes.xyxy, results[0].boxes.cls
        shape = im0.shape[0]
        im0 = Image.fromarray(cv2.cvtColor(im0, cv2.COLOR_BGR2RGB))
        for xyxy, conf, num in zip(boxes, confs, cls_num):
            conf = float(conf) * 100
            label_name = names[int(num)]
            label_name_ch = mapping_ch[label_name]
            im0 = plot_one_box_only_pil(xyxy=xyxy, img=im0, label=f'{label_name_ch} {conf:.2f}%', color=colors[label_name], line_thickness=int(shape / 250))
            
            if args.write_csv:
                csv_writer.writerow([timestamp, label_name, list(map(int, xyxy.tolist())), f"{conf:.2f}%"])  

        im0 = cv2.cvtColor(np.asarray(im0), cv2.COLOR_RGB2BGR)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        pipe.stdin.write(im0.tobytes())
    
    cap.release()
    pipe.terminate()
    
    if args.write_csv:
        csv_file.close()
        print(f"Detection results saved to {args.csv_path}")

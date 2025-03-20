import argparse
import subprocess
import os
import cv2
import random
import csv
from ultralytics import YOLO

def plot_one_box(x, img, color=None, label=None, line_thickness=None):
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

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
        for xyxy, conf, num in zip(boxes, confs, cls_num):
            conf = float(conf) * 100
            label_name = names[int(num)]
            plot_one_box(xyxy, im0, label=f'{label_name} {conf:.2f}%', color=colors[label_name], line_thickness=int(im0.shape[0] / 250))
            
            if args.write_csv:
                csv_writer.writerow([timestamp, label_name, list(map(int, xyxy.tolist())), f"{conf:.2f}%"])  

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        pipe.stdin.write(im0.tobytes())
    
    cap.release()
    pipe.terminate()
    
    if args.write_csv:
        csv_file.close()
        print(f"Detection results saved to {args.csv_path}")

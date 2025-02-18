import argparse
import subprocess
import os
import cv2
import random
from ultralytics import YOLO

def plot_one_box(x, img, color=None, label=None, line_thickness=None):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Stream Processing with YOLO")
    parser.add_argument("--input_stream", type=str, default="rtmp://localhost:1935/obs/stream", 
                        help="RTMP input stream URL")
    parser.add_argument("--output_stream", type=str, default="rtmp://localhost:1935/output/stream", 
                        help="RTMP output stream URL")
    parser.add_argument("--ffmpeg_path", type=str, default=r"D:/VideoStream/ffmpeg-N-102557-g11b489d592-win64-gpl/bin/ffmpeg.exe",
                        help="Path to the ffmpeg executable")
    parser.add_argument("--yolo_model_path", type=str, default="yolo-train/train/weights/best.pt",
                        help="Path to the YOLO model weights")
    args = parser.parse_args()

    input_stream = args.input_stream
    output_stream = args.output_stream
    ffmpeg_path = args.ffmpeg_path
    yolo_model_path = args.yolo_model_path

    # 检查 ffmpeg_path 是否存在
    if not os.path.isfile(ffmpeg_path):
        print(f"Warning: Specified ffmpeg_path '{ffmpeg_path}' not found. Using 'ffmpeg' instead.")
        ffmpeg_path = 'ffmpeg'

    # 检查 YOLO 模型路径是否存在
    if not os.path.isfile(yolo_model_path):
        print(f"Error: YOLO model path '{yolo_model_path}' not found.")
        exit(1)

    cap = cv2.VideoCapture(input_stream)

    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    sizeStr = f"{size[0]}x{size[1]}"

    command = [
        ffmpeg_path,
        '-y', '-an',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', sizeStr,
        '-r', str(cap.get(cv2.CAP_PROP_FPS)),
        '-i', '-',
        '-tune', 'zerolatency',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'ultrafast',
        '-f', 'flv',
        output_stream
    ]

    pipe = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE)

    model = YOLO(yolo_model_path)  # Load YOLO model
    names = model.model.names
    colors = {label: [random.randint(0, 255) for _ in range(3)] for label in set(names.values())}

    while True:
        ret, im0 = cap.read()
        if not ret:
            print("Video frame is empty or video processing has been successfully completed.")
            break

        results = model.predict(im0)
        confs, boxes, cls_num = results[0].boxes.conf, results[0].boxes.xyxy, results[0].boxes.cls
        for xyxy, conf, num in zip(boxes, confs, cls_num):
            conf = float(conf) * 100
            label_name = f'{names[int(num)]} {conf:.2f}%' 
            plot_one_box(xyxy, im0, label=label_name, color=colors[names[int(num)]], line_thickness=int(im0.shape[0] / 250))

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        pipe.stdin.write(im0.tobytes())

    cap.release()
    pipe.terminate()

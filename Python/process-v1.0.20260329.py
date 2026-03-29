import argparse
import subprocess
import os
import cv2
import random
import csv
import yaml
import numpy as np
import time
import asyncio
import websockets
import json
from datetime import datetime
from threading import Thread
from queue import Queue
from ultralytics import YOLO
from plot_result.plot import plot_one_box_only_pil
from PIL import Image

def load_config(path, model_name):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config.get(model_name, {})
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def initialize_stream(input_stream):
    """初始化视频流捕获，失败返回None"""
    cap = cv2.VideoCapture(input_stream)
    if cap.isOpened():
        return cap
    else:
        cap.release()
        return None

def initialize_ffmpeg(ffmpeg_path, size, fps, output_stream):
    """初始化FFmpeg推流管道"""
    sizeStr = f"{size[0]}x{size[1]}"
    command = [
        ffmpeg_path, '-y', '-an', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', sizeStr, '-r', str(fps), '-i', '-', '-tune', 'zerolatency', '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p', '-preset', 'ultrafast', '-f', 'flv', output_stream
    ]
    try:
        pipe = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE)
        return pipe
    except Exception as e:
        print(f"FFmpeg启动失败: {e}")
        return None

# NEW: WebSocket 异步推送协程
async def websocket_sender(uri, data_queue):
    reconnect_interval = 2  # 连接失败2秒重连
    while True:
        try:
            async with websockets.connect(uri, ping_interval=None) as websocket:
                print(f"[WebSocket] 已连接到服务器: {uri}")
                while True:
                    if not data_queue.empty():
                        data = data_queue.get()
                        await websocket.send(json.dumps(data, ensure_ascii=False))
                        print(f"[WebSocket] 推送成功: {data}")
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[WebSocket] 连接断开: {e}, {reconnect_interval}秒后重连...")
            await asyncio.sleep(reconnect_interval)

# NEW: WebSocket 线程启动函数
def start_websocket_thread(uri, data_queue):
    asyncio.run(websocket_sender(uri, data_queue))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Stream Processing with YOLO + WebSocket Push")
    parser.add_argument("--input_stream", type=str, default="rtmp://121.194.59.118:1935/uav_local_mp4/uav_local_mp4?sign=41db35390ddad33f83944f44b8b75ded", 
                        help="RTMP input stream URL")
    parser.add_argument("--output_stream", type=str, default="rtmp://121.194.59.118:1935/uav_detect_stream/uav_detect_stream?sign=41db35390ddad33f83944f44b8b75ded", 
                        help="RTMP output stream URL")
    parser.add_argument("--ffmpeg_path", type=str, default=r"D:/VideoStream/ffmpeg/bin/ffmpeg.exe",
                        help="Path to the ffmpeg executable")
    parser.add_argument("--yolo_model_path", type=str, default="yolo-train/train/weights/best.pt",
                        help="Path to the YOLO model weights")
    parser.add_argument("--write_csv", type=bool, default=False,
                        help="Whether to write detection results to CSV")
    parser.add_argument("--csv_path", type=str, default="output.csv",
                        help="Path to save the CSV file")
    parser.add_argument("--model_name", type=str, default="construction_detect_construction_mengft-v1.0.20250402",
                        help="model name in config/plot_name_ch.yml")
    # NEW: WebSocket 相关参数
    parser.add_argument("--enable_websocket", type=bool, default=True,
                        help="Enable WebSocket push detection results")
    parser.add_argument("--websocket_uri", type=str, default="ws://127.0.0.1:8765",
                        help="WebSocket server URI (ws://ip:port)")
    args = parser.parse_args()

    # 检查 ffmpeg_path 是否存在
    ffmpeg_path = args.ffmpeg_path
    if not os.path.isfile(args.ffmpeg_path):
        print(f"Warning: Specified ffmpeg_path '{args.ffmpeg_path}' not found. Using 'ffmpeg' instead.")
        ffmpeg_path = 'ffmpeg'

    # 加载模型和配置（只加载一次）
    print("正在加载YOLO模型...")
    mapping_ch = load_config(path="config/plot_name_ch.yml", model_name=args.model_name)
    model = YOLO(args.yolo_model_path)
    names = model.model.names
    colors = {label: [random.randint(0, 255) for _ in range(3)] for label in set(names.values())}
    print("YOLO模型加载完成！")

    # CSV初始化
    csv_file = None
    csv_writer = None
    if args.write_csv:
        csv_file = open(args.csv_path, mode='w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Timestamp", "Class", "Coordinates", "Confidence"])

    # NEW: WebSocket 初始化（队列 + 线程）
    websocket_queue = Queue()
    if args.enable_websocket:
        websocket_thread = Thread(target=start_websocket_thread, args=(args.websocket_uri, websocket_queue), daemon=True)
        websocket_thread.start()
        print(f"[WebSocket] 服务已启动，目标地址: {args.websocket_uri}")

    # NEW: WebSocket 推送控制（每1秒推送一次）
    last_websocket_push_time = 0
    websocket_push_interval = 1  # 固定1秒推送1次

    # 全局变量
    cap = None
    pipe = None
    fps = 25  # 默认帧率
    size = (1280, 720)  # 默认分辨率
    reconnect_interval = 3  # 流断开后，3秒重连一次
    frame_count = 0

    print(f"启动推流服务，等待视频流接入: {args.input_stream}")
    print(f"输出推流地址: {args.output_stream}")
    print("按 Q 键退出程序")

    try:
        while True:
            # ===================== 流状态检测与重连逻辑 =====================
            # 如果流未打开，尝试初始化
            if cap is None or not cap.isOpened():
                print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 视频流未连接，{reconnect_interval}秒后重试...")
                time.sleep(reconnect_interval)
                
                # 尝试重新连接输入流
                cap = initialize_stream(args.input_stream)
                if cap is not None:
                    # 获取流参数
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
                    size = (w, h)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 视频流已连接！分辨率: {size}, 帧率: {fps}")
                    
                    # 重启FFmpeg推流
                    if pipe is not None:
                        pipe.terminate()
                        pipe.wait()
                    pipe = initialize_ffmpeg(ffmpeg_path, size, fps, args.output_stream)
                    frame_count = 0  # 重置帧计数
                continue

            # ===================== 正常读取并处理帧 =====================
            ret, im0 = cap.read()
            
            # 帧读取失败（流断开）
            if not ret:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 视频流中断，准备重连...")
                # 释放资源
                cap.release()
                cap = None
                if pipe is not None:
                    pipe.terminate()
                    pipe = None
                continue

            # 首次检测提示
            if frame_count == 0:
                print("<-----------------------模型加载成功，开始检测！---------------------->")
            frame_count += 1

            # 时间戳
            hours = int(frame_count / (fps * 3600))
            minutes = int((frame_count % (fps * 3600)) / (fps * 60))
            seconds = int((frame_count % (fps * 60)) / fps)
            frames = int(frame_count % fps)
            timestamp = f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

            # YOLO检测
            results = model.predict(im0, verbose=False)
            confs, boxes, cls_num = results[0].boxes.conf, results[0].boxes.xyxy, results[0].boxes.cls
            shape = im0.shape[0]
            
            # 转换图像格式
            im0_pil = Image.fromarray(cv2.cvtColor(im0, cv2.COLOR_BGR2RGB))
            
            # 存储当前帧所有检测结果
            current_detections = []

            # 绘制检测框
            for xyxy, conf, num in zip(boxes, confs, cls_num):
                conf_val = float(conf)
                conf_percent = conf_val * 100
                label_name = names[int(num)]
                label_name_ch = mapping_ch.get(label_name, label_name)
                
                # 绘制
                im0_pil = plot_one_box_only_pil(xyxy=xyxy, img=im0_pil, label=f'{label_name_ch} {conf_percent:.2f}%', 
                                                color=colors[label_name], line_thickness=int(shape / 250))
                
                # CSV写入
                if args.write_csv:
                    csv_writer.writerow([timestamp, label_name, list(map(int, xyxy.tolist())), f"{conf_percent:.2f}%"])

                # NEW: 收集检测结果用于WebSocket推送
                current_detections.append({
                    "defect_name": label_name_ch,
                    "score": round(conf_val, 4)
                })

            # 转回OpenCV格式
            im0 = cv2.cvtColor(np.asarray(im0_pil), cv2.COLOR_RGB2BGR)

            # NEW: 每1秒向WebSocket推送一次结果
            current_time = time.time()
            if args.enable_websocket and (current_time - last_websocket_push_time >= websocket_push_interval):
                beijing_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # 构造推送数据
                if len(current_detections) > 0:
                    # 有目标：推送所有目标
                    for det in current_detections:
                        push_data = {
                            "time": beijing_time,
                            "defect_name": det["defect_name"],
                            "score": det["score"],
                            "defect_location": "距离党家庄隧道出口处50米"
                        }
                        websocket_queue.put(push_data)
                last_websocket_push_time = current_time

            # 推流
            if pipe is not None and pipe.stdin is not None:
                try:
                    pipe.stdin.write(im0.tobytes())
                except:
                    print("推流失败，重启FFmpeg...")
                    pipe.terminate()
                    pipe = None

            # 退出检测
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("手动退出程序")
                break

    except KeyboardInterrupt:
        print("\n程序被用户中断(Ctrl+C)")
    finally:
        # 安全释放所有资源
        print("正在关闭资源...")
        if cap is not None:
            cap.release()
        if pipe is not None:
            pipe.terminate()
            pipe.wait()
        if args.write_csv and csv_file is not None:
            csv_file.close()
            print(f"检测结果已保存至: {args.csv_path}")
        cv2.destroyAllWindows()
        print("程序已安全退出")
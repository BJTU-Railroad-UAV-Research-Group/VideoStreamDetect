#!/bin/bash

# 激活 Conda 环境
source ~/anaconda3/etc/profile.d/conda.sh
conda activate jhrs2

# 默认参数值
INPUT_STREAM="rtmp://localhost:1935/obs/stream"
OUTPUT_STREAM="rtmp://localhost:1935/output/stream"
CSV_PATH="output.csv"
FFMPEG_PATH="D:/VideoStream/ffmpeg-N-102557-g11b489d592-win64-gpl/bin/ffmpeg.exe"
YOLO_MODEL_PATH="yolo-train/train/weights/best.pt"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --input_stream)
            INPUT_STREAM="$2"
            shift 2
            ;;
        --output_stream)
            OUTPUT_STREAM="$2"
            shift 2
            ;;
        --csv_path)
            CSV_PATH="$2"
            shift 2
            ;;
        --ffmpeg_path)
            FFMPEG_PATH="$2"
            shift 2
            ;;
        --yolo_model_path)
            YOLO_MODEL_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# 定义运行命令，传入相应参数
COMMAND="python process-v1.0.20250225.py --input_stream $INPUT_STREAM --output_stream $OUTPUT_STREAM --csv_path $CSV_PATH --ffmpeg_path $FFMPEG_PATH --yolo_model_path $YOLO_MODEL_PATH"

# 启动脚本
echo "Starting process-v1.0.20250225.py with input_stream: $INPUT_STREAM, output_stream: $OUTPUT_STREAM, csv_path: $CSV_PATH, ffmpeg_path: $FFMPEG_PATH, yolo_model_path: $YOLO_MODEL_PATH..."
$COMMAND

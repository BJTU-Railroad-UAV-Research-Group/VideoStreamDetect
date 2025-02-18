# 说明文档

## 项目概述

该项目包括一个 `start.sh` 脚本，旨在启动并持续运行 `process.py` 脚本。`process.py` 脚本用于视频流处理、目标检测，并将处理结果推送至指定的流媒体服务。此脚本支持传入多个超参数，用户可以自定义输入流、输出流、FFmpeg路径以及YOLO模型路径。

## 系统要求

- **操作系统**：Linux / macOS / Windows（具有支持 Bash 脚本的环境）
- **软件依赖**：
  - Python 3.x
  - Conda 环境（需要 `jhrs2` 环境）
  - OpenCV 库（`opencv-python`）
  - YOLO 模型及相关库（如 `ultralytics`）
  - FFmpeg（用于视频流处理）

## 安装步骤

1. 克隆项目到本地：

   ```bash
   git clone https://github.com/BJTU-Railroad-UAV-Research-Group/VideoStreamDetect.git
   cd VideoStreamDetect

1. 创建并激活 Conda 环境：

   ```bash
   conda create -n jhrs2 python=3.x
   conda activate jhrs2
   ```

2. 确保你的系统中已安装 FFmpeg。可以从[FFmpeg官方网站](https://ffmpeg.org/download.html)下载并安装。


## 使用说明

### 1. 启动 `start.sh` 脚本

`start.sh` 脚本用于启动 `process.py` 脚本，并支持以下超参数：

- `--input_stream`：输入流的 URL，默认为 `rtmp://localhost:1935/obs/stream`。
- `--output_stream`：输出流的 URL，默认为 `rtmp://localhost:1935/output/stream`。
- `--ffmpeg_path`：FFmpeg 执行文件的路径，默认为 `D:/VideoStream/ffmpeg-N-102557-g11b489d592-win64-gpl/bin/ffmpeg.exe`。
- `--yolo_model_path`：YOLO 模型权重文件的路径，默认为 `yolo-train/train/weights/best.pt`。

#### 启动脚本：

```bash
./start.sh --input_stream "rtmp://your_input_stream" --output_stream "rtmp://your_output_stream" --ffmpeg_path "/path/to/ffmpeg" --yolo_model_path "/path/to/yolo_model.pt"
```

如果不传入某些参数，则会使用默认值。例如：

```bash
./start.sh --input_stream "rtmp://new_input_stream" --yolo_model_path "/new_model/path"
```

这将只更改 `input_stream` 和 `yolo_model_path`，其他参数使用默认值。

### 2. 参数说明

| 参数                | 描述                    | 默认值                                                       |
| ------------------- | ----------------------- | ------------------------------------------------------------ |
| `--input_stream`    | 输入流的 URL            | `rtmp://localhost:1935/obs/stream`                           |
| `--output_stream`   | 输出流的 URL            | `rtmp://localhost:1935/output/stream`                        |
| `--ffmpeg_path`     | FFmpeg 执行文件的路径   | `D:/VideoStream/ffmpeg-N-102557-g11b489d592-win64-gpl/bin/ffmpeg.exe` |
| `--yolo_model_path` | YOLO 模型权重文件的路径 | `yolo-train/train/weights/best.pt`                           |

### 3. 脚本功能

- **`process.py`**：该脚本负责从输入流中读取视频帧，使用 YOLO 模型进行目标检测，并将检测结果通过 FFmpeg 推送到输出流。
- **`start.sh`**：该脚本通过 `python process.py` 启动视频流处理，支持传入超参数，若未传入则使用默认值。并且会无限循环，检测到 `process.py` 异常退出时自动重启。

### 4. 退出脚本

- 若要手动停止脚本，可以按 `Ctrl+C`。

## 常见问题

### 1. FFmpeg 执行路径无法找到怎么办？

确保你的系统中已经正确安装 FFmpeg，并且 `ffmpeg` 可执行文件的路径已在系统环境变量中配置。如果路径不同于默认值，启动脚本时可以使用 `--ffmpeg_path` 参数传入正确的路径。

### 2. YOLO 模型路径不对怎么办？

确保指定的 YOLO 模型路径是正确的，并且权重文件已经存在。如果模型路径不同于默认路径，可以通过 `--yolo_model_path` 参数传入正确的路径。

### 3. 输入流和输出流的配置问题

如果输入流或输出流无法连接或发生错误，检查网络连接是否正常，且流媒体服务是否在运行。

## 贡献

如果你有任何改进建议或 bug 修复，欢迎提交 Pull Request。感谢你对该项目的支持！

## 联系方式

如有任何问题，请通过以下方式联系我：

- 邮箱：ftmeng@bjtu.edu.cn
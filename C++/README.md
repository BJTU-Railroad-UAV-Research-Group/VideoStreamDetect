# YOLOv8 OpenVINO Inference in C++ 🦾

Welcome to the YOLOv8 OpenVINO Inference example in C++! This guide will help you get started with leveraging the powerful YOLOv8 models using OpenVINO and OpenCV API in your C++ projects. Whether you're looking to enhance performance or add flexibility to your applications, this example has got you covered.

## 🌟 Features

- 🚀 **Model Format Support**: Compatible with `ONNX` and `OpenVINO IR` formats.
- ⚡ **Precision Options**: Run models in `FP32`, `FP16`, and `INT8` precisions.
- 🔄 **Dynamic Shape Loading**: Easily handle models with dynamic input shapes.

## 📋 Dependencies

To ensure smooth execution, please make sure you have the following dependencies installed:

| Dependency | Version  |
| ---------- | -------- |
| OpenVINO   | >=2023.3 |
| OpenCV     | >=4.5.0  |
| C++        | >=14     |
| CMake      | >=3.12.0 |

## ⚙️ Build Instructions

Follow these steps to build the project:

1. Clone the repository:

   ```bash
   git clone https://github.com/ultralytics/ultralytics.git
   cd ultralytics/YOLOv8-OpenVINO-CPP-Inference
   ```

2. Create a build directory and compile the project:
   ```bash
   mkdir build
   cd build
   cmake ..
   make
   ```

## 🛠️ Usage

Once built, you can run inference on an image using the following command:

```bash
./detect <model_path.{onnx, xml}> <image_path.jpg>
```

## 🔄 Exporting YOLOv8 Models

To use your YOLOv8 model with OpenVINO, you need to export it first. Use the command below to export the model:

```bash
yolo export model=yolov8s.pt imgsz=640 format=openvino
```

## 📸 Screenshots

### Running Using OpenVINO Model

![Running OpenVINO Model](https://github.com/ultralytics/ultralytics/assets/76827698/2d7cf201-3def-4357-824c-12446ccf85a9)

### Running Using ONNX Model

![Running ONNX Model](https://github.com/ultralytics/ultralytics/assets/76827698/9b90031c-cc81-4cfb-8b34-c619e09035a7)

## ❤️ Contributions

We hope this example helps you integrate YOLOv8 with OpenVINO and OpenCV into your C++ projects effortlessly. Happy coding! 🚀

**上述为`Ultralytics`官方教程，需要注意一些点见下面内容**

------



# OpenCV 4.5+版本的安装与配置（经测试验证4.2版本也可以使用）

## 1.从源码编译安装

### **步骤 1：下载并编译 OpenCV 4.5.0**

```bash
cd ~
git clone -b 4.5.0 https://github.com/opencv/opencv.git
git clone -b 4.5.0 https://github.com/opencv/opencv_contrib.git
mkdir -p opencv/build
cd opencv/build
```

### **步骤 2：编译 OpenCV 4.5.0**

```bash
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/opencv-4.5.0 \
      -DOPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
      -DBUILD_SHARED_LIBS=ON ..
```

然后编译安装：

```bash
make -j$(nproc)
sudo make install
```

这样，OpenCV 4.5.0 就被安装在 **`/opt/opencv-4.5.0`** 目录下，与原来的旧版本不会冲突。

### **步骤3：编译时可选择使用具体的版本**（推荐使用下面的方式2）

### **方式 1：使用 `pkg-config` 选择 OpenCV 版本**

编译 C++ 代码时：

```bash
PKG_CONFIG_PATH=/opt/opencv-4.5.0/lib/pkgconfig pkg-config --cflags --libs opencv4
```

或者：

```bash
g++ my_program.cpp -o my_program `PKG_CONFIG_PATH=/opt/opencv-4.5.0/lib/pkgconfig pkg-config --cflags --libs opencv4`
```

### **方式 2：使用 CMake 选择 OpenCV 版本**

创建 `CMakeLists.txt`：

```bash
cmake_minimum_required(VERSION 3.10)
project(TestOpenCV)

set(OpenCV_DIR "/opt/opencv-4.5.0/lib/cmake/opencv4")  # 指定 OpenCV 4.5.0 的路径
find_package(OpenCV REQUIRED)

add_executable(test test.cpp)
target_link_libraries(test ${OpenCV_LIBS})
```

然后编译：

```bash
cmake -B build -S .
cmake --build build
```

### **方式 3：手动指定 OpenCV 头文件和库路径**

如果你使用 `g++` 直接编译：

```bash
g++ test.cpp -o test -I/opt/opencv-4.5.0/include/opencv4 \
             -L/opt/opencv-4.5.0/lib -lopencv_core -lopencv_imgproc -lopencv_highgui
```

这样就会使用 **OpenCV 4.5.0** 而不是系统默认的版本。

## 2.使用 prebuilt（预编译）OpenCV 4.5.0（未测试）

### **下载 OpenCV 4.5.0 预编译版**

你可以从 OpenCV 官网下载预编译的 OpenCV 4.5.0 版本：

- **OpenCV 官网**: https://opencv.org/releases/
- **GitHub 预编译包**: https://github.com/opencv/opencv/releases/tag/4.5.0

下载后，解压到 `/opt/opencv-4.5.0`（或者其他路径）：

```bash
mkdir -p /opt/opencv-4.5.0
tar -xvf opencv-4.5.0-linux-x64.tar.gz -C /opt/opencv-4.5.0 --strip-components=1
```

# OpenVino版本

安装与配置见[链接地址](https://docs.openvino.ai/2025/get-started/install-openvino/install-openvino-archive-linux.html)

# FFmpeg（推流工具）安装

```bash
sudo apt-get install ffmpeg libavcodec-dev libavformat-dev libswscale-dev
```



# 编译与运行

### 1.编译

根据需求注释选择`CMakeList.txt`中的内容，以`rtsp`接流推流为例

```BASH
cd build
cmake -D WITH_FFMPEG=ON ..
make -j$(nproc)
```

### 2.运行

```bash
./yolo_rtmp {model.onnx} {rtmp://your_rtmp_server/live/input} {rtmp://your_rtmp_server/live/output}
```

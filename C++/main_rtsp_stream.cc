#include "inference.h"
#include <opencv2/highgui.hpp>
#include <opencv2/videoio.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>

int main(int argc, char **argv) {
    // 检查参数个数
    if (argc != 4) {
        std::cerr << "usage: " << argv[0] << " <model_path> <rtsp_input_url> <rtsp_output_url>" << std::endl;
        return 1;
    }
    
    // 获取模型路径、输入和输出RTSP流的URL
    const std::string model_path = argv[1];
    const std::string rtsp_input_url = argv[2];
    const std::string rtsp_output_url = argv[3];

    // 使用OpenCV读取RTSP流
    cv::VideoCapture cap(rtsp_input_url);
    if (!cap.isOpened()) {
        std::cerr << "ERROR: Unable to open RTSP stream: " << rtsp_input_url << std::endl;
        return 1;
    }

    // 获取视频流的帧宽和帧高
    int frame_width = (int)cap.get(cv::CAP_PROP_FRAME_WIDTH);
    int frame_height = (int)cap.get(cv::CAP_PROP_FRAME_HEIGHT);
    int fps = static_cast<int>(cap.get(cv::CAP_PROP_FPS));
    if (fps <= 0) fps = 25;  // 防止FPS为0

    // 2. 启动 FFmpeg 进程，推送到 RTSP
    std::string ffmpeg_cmd = "ffmpeg -y -f rawvideo -pix_fmt bgr24 -s " +
                             std::to_string(frame_width) + "x" + std::to_string(frame_height) +
                             " -r " + std::to_string(fps) +
                             " -i - -c:v libx264 -preset ultrafast -tune zerolatency -rtsp_transport tcp -f rtsp " +
                             rtsp_output_url;

    FILE* ffmpeg_pipe = popen(ffmpeg_cmd.c_str(), "w");
    if (!ffmpeg_pipe) {
        std::cerr << "ERROR: Failed to open FFmpeg pipe!" << std::endl;
        return -1;
    }

    // 3. 初始化 YOLO 推理
    float confidence_threshold = 0.5;
    float NMS_threshold = 0.5;
    yolo::Inference inference(model_path, cv::Size(640, 640), confidence_threshold, NMS_threshold);

    cv::Mat frame;
    while (true) {
        cap >> frame;
        if (frame.empty()) break;

        inference.RunInference(frame);  // YOLO 推理

        // 4. 通过管道发送数据到 FFmpeg
        fwrite(frame.data, 1, frame.total() * frame.elemSize(), ffmpeg_pipe);

        // 本地显示（可选）
        cv::imshow("YOLO RTSP Stream", frame);
        if (cv::waitKey(1) == 27) break; // ESC 退出
    }

    // 释放资源
    cap.release();
    pclose(ffmpeg_pipe);
    cv::destroyAllWindows();
    return 0;
}
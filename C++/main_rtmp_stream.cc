#include "inference.h"
#include <iostream>
#include <opencv2/highgui.hpp>
#include <opencv2/videoio.hpp>
#include <cstdio>

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: " << argv[0] << " <model_path> <rtmp_input_url> <rtmp_output_url>" << std::endl;
        return 1;
    }

    std::string model_path = argv[1];
    std::string rtmp_input_url = argv[2];  // RTMP 输入流
    std::string rtmp_output_url = argv[3]; // RTMP 输出流

    // 1. 打开 RTMP 输入流
    cv::VideoCapture cap(rtmp_input_url);
    if (!cap.isOpened()) {
        std::cerr << "ERROR: Failed to open RTMP stream: " << rtmp_input_url << std::endl;
        return -1;
    }

    int frame_width = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_WIDTH));
    int frame_height = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_HEIGHT));
    int fps = static_cast<int>(cap.get(cv::CAP_PROP_FPS));
    if (fps <= 0) fps = 25;  // 防止FPS为0

    // 2. 启动 FFmpeg 进程，用于推流 RTMP
    std::string ffmpeg_cmd = "ffmpeg -y -f rawvideo -pix_fmt bgr24 -s " +
                             std::to_string(frame_width) + "x" + std::to_string(frame_height) +
                             " -r " + std::to_string(fps) +
                             " -i - -c:v libx264 -preset ultrafast -tune zerolatency -f flv " +
                             rtmp_output_url;

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
        cv::imshow("YOLO RTMP Stream", frame);
        if (cv::waitKey(1) == 27) break; // ESC 退出
    }

    // 释放资源
    cap.release();
    pclose(ffmpeg_pipe);
    cv::destroyAllWindows();
    return 0;
}

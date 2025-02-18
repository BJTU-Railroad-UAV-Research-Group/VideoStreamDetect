cmake_minimum_required(VERSION 3.12)
project(yolov8_openvino_example)

set(CMAKE_CXX_STANDARD 14)
set(OpenCV_DIR "/opt/opencv-4.5.0/lib/cmake/opencv4")
find_package(OpenCV REQUIRED)

set(OPENVINO_DIR "/opt/intel/openvino_2025")
include_directories(
	${OpenCV_INCLUDE_DIRS}
	${OPENVINO_DIR}/runtime/include
)

# # either
# add_executable(detect 
# 	main.cc
# 	inference.cc
# )

# or
add_executable(yolo_rtsp 
	main_rtsp_stream.cc	
	inference.cc
)

# # or
# add_executable(yolo_rtmp 
# 	main_rtmp_stream.cc	
# 	inference.cc
# )

target_link_libraries(yolo_rtsp
	${OpenCV_LIBS}
	${OPENVINO_DIR}/runtime/lib/intel64/libopenvino.so
)

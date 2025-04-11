import json
import cv2
import os
import time
import numpy as np
from numpy import random
from PIL import ImageDraw, ImageFont, Image


def plot_one_box_pil(xyxy, img, color=None, label=None, line_thickness=None):
    
    # 将 OpenCV 图像转换为 PIL 图像
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    # 创建 ImageDraw 对象
    draw = ImageDraw.Draw(img_pil)
    
    # 计算默认线条宽度
    tl = line_thickness or round(0.002 * (img_pil.size[0] + img_pil.size[1]) / 2) + 1
    color = color or [random.randint(0, 255) for _ in range(3)]
    
    # 边界框坐标
    c1, c2 = (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3]))
    
    # 绘制矩形框
    draw.rectangle([c1, c2], outline=tuple(color), width=tl)

    if label:
        # 字体设置
        font = ImageFont.truetype("fonts/wqy-zenhei.ttc", size=20)  # 替换为正确的字体路径
        tf = max(tl - 1, 1)  # 字体厚度
        
        # 计算文本的边界框
        bbox = draw.textbbox((0, 0), label, font=font)
        t_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])  # 宽度和高度
        
        # 标签框的底色填充
        label_background = (c1[0], c1[1] - t_size[1] - 3, c1[0] + t_size[0], c1[1])
        draw.rectangle(label_background, fill=tuple(color))
        
        # 在框内绘制文本
        draw.text((c1[0], c1[1] - t_size[1] - 2), label, fill=(255, 255, 255), font=font)
    
    # 返回 OpenCV 格式的图像
    return cv2.cvtColor(np.asarray(img_pil), cv2.COLOR_RGB2BGR)

def read_CN_img(img):
    return cv2.imdecode(np.fromfile(img, dtype=np.uint8), 1)

def dict_to_list(bbox):
    return [bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']]

def save_image_with_encoding(img_name, img):
    success, encoded_image = cv2.imencode(".jpg", img)
    if success:
        try:
            with open(img_name, "wb") as f:
                f.write(encoded_image)
            print(f"图片已成功保存为 {img_name}")
        except Exception as e:
            print(f"保存图片时发生错误: {e}")
    else:
        print("图片编码失败")

def plot(img, response):
    
    try:
        with open(response, "r", encoding="utf-8") as file:
            result = json.load(file)  # 解析 JSON 文件内容
        code = result['code']
        details = result['msg']
        result = result['data']
        ori_img = read_CN_img(img)
        boxes = [r['Box'] for r in result]
        confs = [r['Score'] for r in result]
        labels = [r["inspect_object_type_name"]+"-"+r['defect_type_name'] for r in result]
        colors = {label :[random.randint(0, 255) for _ in range(3)] for label in set(labels)}

        save_dir = 'result'
        os.makedirs(save_dir,exist_ok=True)
        
        save_path = os.path.join(save_dir,f'{int(time.time() * 1000)}.jpg')  # img.jpg

        if len(boxes):
            
            # Write results
            for x1x2y1y2, conf, label in zip(boxes, confs, labels):
                xyxy = dict_to_list(x1x2y1y2)
                label_name = f'{label} {conf:.2f}'
                ori_img = plot_one_box_pil(xyxy, ori_img, label=label_name, color=colors[label], line_thickness=int(ori_img.shape[0] / 250))

        # Save results (image with detections)
        save_image_with_encoding(save_path, ori_img)
        
        print(f" The image with the result is saved in: {save_path}")

    except:
        code = -1
        details = "请查看日志进行解决   测试失败"
        save_path = img
        
    return save_path, code, details


if __name__ == '__main__':

    plot(img="data/00041.jpg", response="data/00041.json")


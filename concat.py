import os
import glob
import time
import datetime
import requests
import subprocess

def get_file_date(file_name):
    # 从文件名中提取日期
    try:
        date_str = file_name.split('-')[0] + file_name.split('-')[1]  # 提取日期
        return datetime.datetime.strptime(date_str[:-4], '%Y%m%d%H')
    except IndexError or ValueError:
        return None

def get_file_suffix(file_name):
    # 从文件名中提取最后一个“-”后的字符串
    try:
        suffix = file_name.split('-')[-1]
        return suffix
    except IndexError:
        return ''

def get_live_status(room_id):   # 输入字符串型房间号
    # 检查直播间状态
    url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }   # "User-Agent"头，是 HTTP 请求头的一部分。它用于标识客户端（通常是浏览器或其他 HTTP 客户端）的软件类型、版本号、以及可能的其他相关信息。
    try:
        response = requests.get(url, headers=headers, verify=True)
        response.raise_for_status()
        # 使用请求头（浏览器和命令行工具发送申请时都会附上请求头）并开启SSL验证，若开启了代理则需要另行设置，否则会访问失败

        data = response.json()
        live_status = int(data['data']['live_status'])
        return live_status  # 返回整型表示的直播间状态，0：未开播，1：直播中，2：轮播中
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def merge_videos(directory):
    # 输入子目录绝对路径，连接flv文件
    flv_files = sorted(glob.glob(os.path.join(directory, '*.flv')), key=os.path.getmtime)

    if not flv_files:
        print(f"No FLV files found in {directory}")
        return

    live_status = get_live_status(os.path.basename(directory).split('-')[0])  # 获取直播间状态

    if live_status == 1:
        print(f"{os.path.basename(directory)}直播间正在直播，不进行合并操作。")
        return

    filename = os.path.splitext(os.path.basename(flv_files[0]))[0]  # 改为纯文件名
    merge_name = f"{get_file_date(filename).strftime('%Y_%m_%d_%H')};{get_file_suffix(filename)};.mp4"  # mp4文件命名格式

    print(f"Merging {len(flv_files)} FLV files into {merge_name}")
    with open('videos.txt', 'w', encoding='UTF-8') as f:
        f.write('\n'.join(f"file '{video}'" for video in flv_files))

    directory_merge_name = directory + "\\" + merge_name
    # os.system(f"ffmpeg -f concat -safe 0 -i videos.txt -c copy -y {directory_merge_name}")    # 未执行完毕就会向下执行，极易出错
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'videos.txt', '-c', 'copy', '-y', directory_merge_name], check=True)    # 命令完成后，程序才向下执行

    # 删除使用的FLV文件
    # for video in flv_files:
    #     os.remove(video)
    #     print(f"Deleted {video}")

if __name__ == "__main__":
    # 注意，使用的录播姬保存文件格式为yyyymmdd-HHMMSS-title.flv
    base_directory = input('输入根目录绝对路径：')
    # base_directory = r"G:\本地资源库\bilibili录播"
    # 录播保存根目录

    while True:
        for sub_directory in os.listdir(base_directory):
            full_path = os.path.join(base_directory, sub_directory)
            if os.path.isdir(full_path):
                merge_videos(full_path)

        print("Waiting for the next round of directory traversal...")
        time.sleep(1200)  # 等待20分钟后进行下一轮遍历
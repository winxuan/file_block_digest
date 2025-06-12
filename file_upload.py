import requests
import os
import base64
import subprocess
import platform
import datetime
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

"""
脚本没有调用企微接口的逻辑，需要自己实现对应的API后使用
如下：
{BASE_URL}/init_large_file_upload
{BASE_URL}/upload_large_file_part
{BASE_URL}/finish_large_file_upload
{BASE_URL}/get_share_url
{BASE_URL}/set_file_share

需要自己补充以下信息
BASE_URL = ""
SPACE_ID = ''
"""

# API根地址
BASE_URL = ""
SPACE_ID = ''
# 本地文件路径
CHUNK_SIZE = 2097152  # 分块大小，2MB
MAX_CONCURRENT_UPLOADS = 10  # 最大并发数

def init_large_file_upload(file_name, file_size, block_sha_list):
    url = f"{BASE_URL}/init_large_file_upload"
    headers = {"Content-Type": "application/json"}
    data = {
        "file_name": file_name,
        "size": file_size,
        "block_sha": block_sha_list,  # 直接使用分块SHA数组
        "spaceid": SPACE_ID,
        "fatherid": SPACE_ID
    }
    print(f"初始化请求: {data}")
    response = requests.post(url, json=data, headers=headers)
    print(f"初始化响应: {response.json()}")
    return response.json()

def upload_large_file_part(upload_key, index, chunk_data):
    url = f"{BASE_URL}/upload_large_file_part"
    headers = {"Content-Type": "application/json"}
    data = {
        "upload_key": upload_key,
        "index": index,
        "file_base64_content": chunk_data
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def finish_large_file_upload(upload_key):
    url = f"{BASE_URL}/finish_large_file_upload"
    headers = {"Content-Type": "application/json"}
    data = {"upload_key": upload_key}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def get_share_url(fileid):
    url = f"{BASE_URL}/get_share_url"
    headers = {"Content-Type": "application/json"}
    data = {"fileid": fileid}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def set_file_share(fileid, auth_scope):
    url = f"{BASE_URL}/set_file_share"
    headers = {"Content-Type": "application/json"}
    data = {
        "fileid": fileid,
        "auth_scope": auth_scope,
        "auth":1
    }
    response = requests.post(url, json=data, headers=headers)
    
    # 根据 auth_scope 打印权限范围描述
    scope_descriptions = {
        1: "指定人",
        2: "企业内",
        3: "企业外",
        4: "企业内需管理员审批（仅有管理员时可设置）",
        5: "企业外需管理员审批（仅有管理员时可设置）"
    }
    if response.json().get("errcode") != 0:
        print(f"设置分享权限失败: {response.json().get('errmsg')}")
        return
    print(f"设置分享权限成功，权限范围: {scope_descriptions.get(auth_scope, '未知')}")
    print(response.json()) 

def calculate_block_sha(file_path):
    system = platform.system()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"系统: {system}")
    
    if system == "Windows":
        # Windows平台调用外部可执行文件
        executable_path = os.path.join(script_dir, "test_file_block_digest.exe")
    elif system == "Darwin":
        # Mac平台调用外部可执行文件
        executable_path = os.path.join(script_dir, "test_file_block_digest_for_mac")
    elif system == "Linux":
        # Linux平台调用外部可执行文件
        executable_path = os.path.join(script_dir, "test_file_block_digest_for_linux")
    else:
        raise NotImplementedError(f"不支持的操作系统: {system}")

    # 调用外部可执行文件
    print(f"调用外部可执行文件: {executable_path}")
    result = subprocess.run([executable_path, file_path], capture_output=True, text=True)
    output = result.stdout
    sha1_list = []
    for line in output.splitlines():
        if "cumulate_sha1" in line:
            print(line)
            sha1 = line.split("cumulate_sha1: ")[1]
            sha1_list.append(sha1)
    return sha1_list

def upload_chunk(upload_key, index, chunk_data):
    part_response = upload_large_file_part(upload_key, index, chunk_data)
    if part_response.get("errcode") != 0:
        print(f"分块 {index} 上传失败: {part_response.get('errmsg')}")
        return False
    return True

def upload_large_file(file_path):
    # 获取文件信息
    file_name, file_ext = os.path.splitext(os.path.basename(file_path))
    time_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{file_name}_{time_suffix}{file_ext}"
    file_size = os.path.getsize(file_path)
    block_sha_list = calculate_block_sha(file_path)

    # 初始化上传
    init_response = init_large_file_upload(file_name, file_size, block_sha_list)
    if init_response.get("errcode") != 0:
        print(f"初始化失败: {init_response.get('errmsg')}")
        return None
    if init_response.get("hit_exist", False):
        print(f"命中秒传，文件ID: {init_response.get('fileid')}")
        return init_response.get("fileid")
    upload_key = init_response.get("upload_key")
    print(f"初始化成功，upload_key: {upload_key}")

    # 分块上传
    chunks = []
    with open(file_path, "rb") as f:
        index = 1
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunk_data = base64.b64encode(chunk).decode("utf-8")
            chunks.append((upload_key, index, chunk_data))
            index += 1

    total_chunks = len(chunks)
    print(f"总块数: {total_chunks}")

    # 并发上传
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_UPLOADS) as executor:
        futures = [executor.submit(upload_chunk, *chunk) for chunk in chunks]
        for future in tqdm(as_completed(futures), total=total_chunks, desc="上传进度"):
            pass

    # 完成上传
    finish_response = finish_large_file_upload(upload_key)
    if finish_response.get("errcode") != 0:
        print(f"完成上传失败: {finish_response.get('errmsg')}")
        return None
    print(f"上传完成，文件ID: {finish_response.get('fileid')}")
    return finish_response.get("fileid")

def generate_random_ascii_file(file_path, size_mb):
    """生成指定大小的随机ASCII文件（优化版）"""
    size_bytes = size_mb * 1024 * 1024
    chunk_size = 1024 * 1024  # 每次生成1MB数据
    with open(file_path, 'w', buffering=chunk_size) as f:
        for _ in range(size_bytes // chunk_size):
            # 生成1MB的随机ASCII字符块
            chunk = ''.join(random.choices(''.join(chr(i) for i in range(32, 127)), k=chunk_size))
            f.write(chunk)
        # 处理剩余不足1MB的部分
        remaining = size_bytes % chunk_size
        if remaining > 0:
            chunk = ''.join(random.choices(''.join(chr(i) for i in range(32, 127)), k=remaining))
            f.write(chunk)

def test():
    # 生成100MB的随机ASCII文件
    time_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    test_file_path = os.path.join(os.path.dirname(__file__), f"test_100mb_{time_suffix}.txt")
    generate_random_ascii_file(test_file_path, 100)
    print(f"已生成测试文件: {test_file_path}")

    # 上传文件
    fileid = upload_large_file(test_file_path)
    if fileid:
        # 设置文件分享权限
        set_file_share(fileid, 2)
        # 获取分享链接
        share_url = get_share_url(fileid)
        print(f"分享链接: {share_url}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test.py <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    fileid = upload_large_file(file_path)
    if fileid:
        # 设置文件分享权限
        set_file_share(fileid, 2)
        # 获取分享链接
        share_url = get_share_url(fileid)
        print(f"分享链接: {share_url}")

if __name__ == "__main__":
    main()
    # test() 
    
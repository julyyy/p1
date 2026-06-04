import os
import shutil
from datetime import datetime

def main():
    base_path = r"C:\E3\Down\pachong"
    
    if not os.path.exists(base_path):
        print(f"[错误] 基础路径不存在: {base_path}")
        return
    
    # 创建时间戳文件夹名称（年月日小时分钟）
    now = datetime.now()
    folder_name = now.strftime("%Y%m%d%H%M")
    output_folder = os.path.join(base_path, folder_name)
    
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"[创建] 新文件夹: {folder_name}")
    else:
        print(f"[警告] 文件夹已存在: {folder_name}")
    
    # 扫描所有 page_N 文件夹
    page_folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith("page_"):
            page_folders.append((item, item_path))
    
    page_folders.sort(key=lambda x: int(x[0].split("_")[1]))
    
    if not page_folders:
        print(f"[警告] 未找到任何page_*文件夹")
        return
    
    print(f"[扫描] 找到 {len(page_folders)} 个文件夹\n")
    
    # 收集所有文件
    total_count = 0
    all_files = []
    
    for page_name, page_path in page_folders:
        for file in os.listdir(page_path):
            file_path = os.path.join(page_path, file)
            if os.path.isfile(file_path) and file.endswith('.jpg'):
                mtime = os.path.getmtime(file_path)
                all_files.append((file_path, file, mtime))
                total_count += 1
    
    if not all_files:
        print(f"[警告] 没有找到任何jpg文件")
        return
    
    # 按修改时间全局排序
    all_files.sort(key=lambda x: x[2])
    
    print(f"[开始] 移动 {len(all_files)} 个文件到 {folder_name}\n")
    
    # 移动文件
    success_count = 0
    for idx, (file_path, file_name, _) in enumerate(all_files, 1):
        dest_path = os.path.join(output_folder, file_name)
        
        try:
            shutil.move(file_path, dest_path)
            print(f"[{idx:3d}/{total_count}] {file_name:20s} 移动完成")
            success_count += 1
        except Exception as e:
            print(f"[失败] 无法移动 {file_name}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"[完成] 成功移动 {success_count}/{len(all_files)} 个文件")
    print(f"[保存] 所有图片已保存到: {folder_name}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

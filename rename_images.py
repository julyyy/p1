import os

def main():
    base_path = r"C:\E3\Down\pachong"
    
    if not os.path.exists(base_path):
        print(f"[错误] 基础路径不存在: {base_path}")
        return
    
    # 扫描所有文件夹
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
    all_files = []
    for page_name, page_path in page_folders:
        for file in os.listdir(page_path):
            file_path = os.path.join(page_path, file)
            if os.path.isfile(file_path):
                mtime = os.path.getmtime(file_path)
                all_files.append((file_path, file, page_name, mtime))
    
    if not all_files:
        print(f"[警告] 没有找到任何文件")
        return
    
    # 按修改时间全局排序
    all_files.sort(key=lambda x: x[3])
    
    print(f"[开始] 全局重命名 {len(all_files)} 个文件\n")
    
    # 按顺序重命名
    for idx, (file_path, old_name, page_name, _) in enumerate(all_files, 1):
        ext = os.path.splitext(old_name)[1]
        new_name = f"{idx:03d}{ext}"
        new_path = os.path.join(os.path.dirname(file_path), new_name)
        
        if os.path.exists(new_path) and new_path != file_path:
            print(f"[警告] 目标文件已存在，跳过: {new_name}")
            continue
        
        try:
            os.rename(file_path, new_path)
            print(f"[{idx:3d}/377] {page_name:8s} {old_name[:30]:30s} → {new_name}")
        except Exception as e:
            print(f"[失败] 无法重命名 {old_name}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"[完成] 所有文件全局重命名完毕 (001-{len(all_files):03d})")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

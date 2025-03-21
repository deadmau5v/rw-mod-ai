import zipfile
import os

# mods = os.listdir("data/mods_rwmod")

# for mod in mods:
#     path = f"data/mods_rwmod/{mod}"
#     filename = os.path.basename(path)
#     try:
#         print(path)
#         if os.path.isfile(path):
#             with zipfile.ZipFile(path, "r") as zip_ref:
#                 zip_ref.extractall(f"data/mods/{filename}")
#     except Exception as e:
#         print(path, e)

# 只保留ini文件和png文件
# 使用逐渐增加的id命名 放到 data/ini 和 data/png 目录下
# 考虑到多级目录


id_ = 1


os.makedirs("data/ini", exist_ok=True)
os.makedirs("data/png", exist_ok=True)


def save_ini_file(path):
    global id_
    if os.path.isfile(path):
        if os.path.basename(path).endswith(".ini"):
            os.rename(path, f"data/ini/{id_}.ini")
            id_ += 1
    else:
        for file in os.listdir(path):
            save_ini_file(f"{path}/{file}")


save_ini_file("data/mods")

# 只保留png文件
# 使用逐渐增加的id命名 放到 data/png 目录下

id_ = 1


def save_png_file(path):
    global id_

    if os.path.isfile(path):
        if os.path.basename(path).endswith(".png"):
            os.rename(path, f"data/png/{id_}.png")
            id_ += 1
    else:
        for file in os.listdir(path):
            save_png_file(f"{path}/{file}")


save_png_file("data/mods")

import os
import re
import opencc

def main():
    while True:
        print("===============")
        print("戴森球計畫新增繁體中文工具")
        print("===============")
        print("1. 新增繁體中文")
        print("2. 選繁體中文時語音改為英文語音")
        print("3. 選繁體中文時恢復為中文語音")
        print("4. 離開程式")
        print("===============")
        choice = input("請輸入選項: ").strip()

        if choice == "1":
            run_converter()
            input("\n繁體中文新增完成。按 Enter 返回主選單...")
        elif choice == "2":
            switch_voice(lang="en")
            input("\n繁體中文改為使用英文語音。按 Enter 返回主選單...")
        elif choice == "3":
            switch_voice(lang="zh")
            input("\n繁體中文已恢復為中文語音。按 Enter 返回主選單...")
        elif choice == "4":
            print("程式已結束。")
            break
        else:
            print("請輸入 1、2、3 或 4。")

def run_converter():
    # 建立轉換器(簡體 -> 繁體)
    converter = opencc.OpenCC('s2twp')

    # 原始檔案資料夾(簡體)
    input_folder = r"Locale\2052"

    # 輸出資料夾(繁體)
    output_folder = r"Locale\1029"

    # Header.txt 路徑
    header_path = r"Locale\Header.txt"

    # 如果輸出資料夾不存在,就自動建立
    os.makedirs(output_folder, exist_ok=True)

    # 創建/覆蓋 Header.txt（保留中間那一行空行，並確保檔尾有換行）
    header_content = """[Localization Project]
Version=1.1
2052,简体中文,zhCN,zh,1033,1
1033,English,enUS,en,2052,0
1036,français,frFR,fr,1033,0,0
1031,Deutsch,deDE,de,1033,0,0
1041,日本語,jaJA,ja,1033,1,0
1042,한국어,koKO,ko,1033,1,0
1029,繁體中文,zhTW,zh_TW,1033,1

base=0
combat=0
creation=0
prototype=-1
dictionary=3
parameters=0
[outsource]=-6
[user]=-9
"""
    with open(header_path, "w", encoding="utf-8", newline="\n") as header_file:
        # 若最末無換行，補上一個
        if not header_content.endswith("\n"):
            header_content += "\n"
        header_file.write(header_content)
    print("\nHeader.txt 已創建於:", header_path)

    # 處理轉換檔案
    for file in os.listdir(input_folder):
        if file.endswith(".txt"):
            input_path = os.path.join(input_folder, file)
            output_path = os.path.join(output_folder, file)

            print(f"正在處理：{file}")
            with open(input_path, "r", encoding="utf-16 LE") as fin:
                lines = fin.readlines()

            converted_lines = []
            for line in lines:
                parts = line.split('\t', 2)
                if len(parts) == 3:
                    parts[2] = converter.convert(parts[2])
                    converted_line = '\t'.join(parts)
                else:
                    converted_line = line
                converted_lines.append(converted_line)

            with open(output_path, "w", encoding="utf-16 LE") as fout:
                fout.writelines(converted_lines)

    print("\n繁體中文新增完成，結果已輸出到:", output_folder)

def switch_voice(lang="en"):
    """
    解析 base.txt 每行為「鍵 名 / 數字 / 值」，只替換特定鍵的值。
    lang="en" 會切到英文資源；lang="zh" 會切回中文資源。
    """
    base_path = r"Locale\1029\base.txt"
    if not os.path.exists(base_path):
        print("找不到 base.txt，請確認路徑是否正確。")
        return

    with open(base_path, "r", encoding="utf-16 LE") as f:
        lines = f.readlines()

    row_pat = re.compile(r'^(\S+)\s+(\d+)\s+(.*?)(\r?\n)?$')

    # 兩組目標值
    value_map_en = {
        "ImageLogo0": "UI/Textures/dsp-logo-en",
        "ImageLogo1": "UI/Textures/dsp-logo-flat-en",
        "ImageLogo2": "UI/Textures/dsp-logo-flat-en",
        "AudioResPostfix": "-en",
        "CutsceneBGM0": "Musics/df-cutscene-en",
    }
    value_map_zh = {
        "ImageLogo0": "UI/Textures/dsp-logo-zh",
        "ImageLogo1": "UI/Textures/dsp-logo-flat-zh",
        "ImageLogo2": "UI/Textures/dsp-logo-flat-zh-c",
        "AudioResPostfix": "-zh",
        "CutsceneBGM0": "Musics/df-cutscene-zh",
    }
    value_map = value_map_en if lang == "en" else value_map_zh

    out_lines = []
    for line in lines:
        m = row_pat.match(line)
        if not m:
            out_lines.append(line)
            continue
        key, number, value, newline = m.group(1), m.group(2), m.group(3), m.group(4) or "\n"
        if key in value_map:
            value = value_map[key]
        # 規範化輸出格式（鍵 \t\t 數字 \t 值）
        out_lines.append(f"{key}\t\t{number}\t{value}{newline}")

    with open(base_path, "w", encoding="utf-16 LE") as f:
        f.writelines(out_lines)

    if lang == "en":
        print("\nbase.txt 已修改為英文語音設定。")
    else:
        print("\nbase.txt 已恢復為中文語音設定。")

if __name__ == "__main__":
    main()

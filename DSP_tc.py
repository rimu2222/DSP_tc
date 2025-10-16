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
    """將 Locale\\2052 內 UTF-16 LE .txt 的第三欄做簡轉繁，並保留原分隔與行尾"""
    converter = opencc.OpenCC('s2tw')

    input_folder = r"Locale\2052"
    output_folder = r"Locale\1029"
    header_path = r"Locale\Header.txt"

    os.makedirs(output_folder, exist_ok=True)

    # 產生 Header.txt（保留中間那一行空行，並確保檔尾有換行）
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
        if not header_content.endswith("\n"):
            header_content += "\n"
        header_file.write(header_content)
    print("\nHeader.txt 已創建於:", header_path)

    # 正則：鍵(非tab/換行) + 分隔1(tab/空白+)
    #     + 數字 + 分隔2(tab/空白+) + 值(可為空) + 行尾(\n 或 \r\n，可無)
    row_pat = re.compile(r'^([^\t\r\n]+)([\t ]+)(\d+)([\t ]+)(.*?)(\r?\n)?$')

    for file in os.listdir(input_folder):
        if not file.endswith(".txt"):
            continue
        input_path = os.path.join(input_folder, file)
        output_path = os.path.join(output_folder, file)

        print(f"正在處理：{file}")
        with open(input_path, "r", encoding="utf-16 LE") as fin:
            lines = fin.readlines()

        out_lines = []
        for line in lines:
            m = row_pat.match(line)
            if not m:
                # 例如空行、註解或非標準列：原樣保留
                out_lines.append(line)
                continue

            key, sep1, number, sep2, value, eol = m.groups()
            # 只轉第三欄內容
            new_value = converter.convert(value)
            # 完整保留分隔符與原行尾（若原本沒有行尾，就不要硬加）
            out_lines.append(f"{key}{sep1}{number}{sep2}{new_value}{(eol or '')}")

        with open(output_path, "w", encoding="utf-16 LE") as fout:
            fout.writelines(out_lines)

    print("\n繁體中文新增完成，結果已輸出到:", output_folder)

def switch_voice(lang="en"):
    """
    解析 base.txt 每行為「鍵 名 / 數字 / 值」，只替換特定鍵的值。
    lang="en" 會切到英文資源；lang="zh" 會切回中文資源。
    保留原始分隔與行尾格式。
    """
    base_path = r"Locale\1029\base.txt"
    if not os.path.exists(base_path):
        print("找不到 base.txt，請確認路徑是否正確。")
        return

    with open(base_path, "r", encoding="utf-16 LE") as f:
        lines = f.readlines()

    row_pat = re.compile(r'^([^\t\r\n]+)([\t ]+)(\d+)([\t ]+)(.*?)(\r?\n)?$')

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

        key, sep1, number, sep2, value, eol = m.groups()
        # 有在表上的鍵才改第三欄；其餘照舊
        if key in value_map:
            value = value_map[key]
        out_lines.append(f"{key}{sep1}{number}{sep2}{value}{(eol or '')}")

    with open(base_path, "w", encoding="utf-16 LE") as f:
        f.writelines(out_lines)

    if lang == "en":
        print("\nbase.txt 已修改為英文語音設定。")
    else:
        print("\nbase.txt 已恢復為中文語音設定。")

if __name__ == "__main__":
    main()

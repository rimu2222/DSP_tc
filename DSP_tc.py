import os
import re
import sys
import opencc
from collections import OrderedDict

# 檔名設定
REPLACE_LIST_FILENAME = "replace_list.txt"        # 第三欄字串替換：每行「原字串,新字串」
KEY_VALUE_LIST_FILENAME = "key_value_list.txt"    # 依第一欄覆寫第三欄：每行「key,new_value」

def main():
    while True:
        print("===============")
        print("戴森球計畫新增繁體中文工具")
        print("===============")
        print("1. 新增繁體中文")
        print("2. 選繁體中文時語音改為英文語音")
        print("3. 選繁體中文時恢復為中文語音")
        print("4. 選繁體中文時語音改為日文語音")
        print("5. 離開程式")
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
            switch_voice(lang="ja")
            input("\n繁體中文改為使用日文語音。按 Enter 返回主選單...")
        elif choice == "5":
            print("程式已結束。")
            break
        else:
            print("請輸入 1、2、3、4 或 5。")

def _read_pairs_from_file(path):
    """讀取取代表：每行「old,new」，回傳 list[(old,new)]。支援空行與 # 註解；只切第一個逗號。"""
    pairs = []
    if not path or not os.path.exists(path):
        return pairs
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "," not in line:
                    print(f"取代表第 {lineno} 行格式不正確（缺少逗號）：{raw.rstrip()}")
                    continue
                old, new = line.split(",", 1)
                pairs.append((old, new))
    except Exception as e:
        print(f"讀取取代表失敗：{path}，原因：{e}")
    return pairs

def _read_key_map_from_file(path):
    """讀取 key→new_value 覆寫表：每行「key,new_value」，回傳 OrderedDict[key]=new_value。"""
    d = OrderedDict()
    if not path or not os.path.exists(path):
        return d
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "," not in line:
                    print(f"key_value 表第 {lineno} 行格式不正確（缺少逗號）：{raw.rstrip()}")
                    continue
                k, v = line.split(",", 1)
                d[k] = v
    except Exception as e:
        print(f"讀取 key_value 表失敗：{path}，原因：{e}")
    return d

def _meipass_dir():
    """PyInstaller 封裝資源目錄（展開目錄）。未封裝時回傳 None。"""
    return getattr(sys, "_MEIPASS", None)

def _script_dir():
    """EXE 同層 / .py 同層目錄。"""
    return os.path.dirname(os.path.abspath(__file__))

def load_replace_pairs():
    """
    載入第三欄字串取代表，優先順序（後者覆蓋前者）：
    1) 封裝內 replace_list.txt（_MEIPASS）
    2) EXE 同層 replace_list.txt
    """
    merged = OrderedDict()

    meipass = _meipass_dir()
    if meipass:
        bundled_path = os.path.join(meipass, REPLACE_LIST_FILENAME)
        for o, n in _read_pairs_from_file(bundled_path):
            merged[o] = n

    user_path = os.path.join(_script_dir(), REPLACE_LIST_FILENAME)
    for o, n in _read_pairs_from_file(user_path):
        merged[o] = n

    if merged:
        print(f"已載入 {len(merged)} 筆第三欄字串取代規則。")
    else:
        print("未找到第三欄字串取代表，將略過此步驟。")
    return list(merged.items())

def load_key_overrides():
    """
    載入 key→new_value 覆寫表，優先順序（後者覆蓋前者）：
    1) 封裝內 key_value_list.txt（_MEIPASS）
    2) EXE 同層 key_value_list.txt
    """
    merged = OrderedDict()

    meipass = _meipass_dir()
    if meipass:
        bundled_path = os.path.join(meipass, KEY_VALUE_LIST_FILENAME)
        kv = _read_key_map_from_file(bundled_path)
        merged.update(kv)

    user_path = os.path.join(_script_dir(), KEY_VALUE_LIST_FILENAME)
    kv2 = _read_key_map_from_file(user_path)
    merged.update(kv2)

    if merged:
        print(f"已載入 {len(merged)} 筆 key→第三欄覆寫規則。")
    else:
        print("未找到 key 覆寫表，將略過此步驟。")
    return merged  # OrderedDict

def run_converter():
    """
    將 Locale\\2052 內 UTF-16 LE .txt 的第三欄做簡轉繁，
    → 套用 replace_list.txt 對第三欄做字串取代，
    → 若 key 在 key_value_list.txt 內，直接覆寫第三欄（最高優先）。
    保留原分隔（空白/Tab）與行尾（LF/CRLF）。
    修改原有 Header.txt 加入繁體中文語系，並加入防重複檢查。
    """
    converter = opencc.OpenCC('s2twp')

    replace_pairs = load_replace_pairs()     # list[(old,new)]
    key_overrides = load_key_overrides()     # dict[key]=new_value

    input_folder = r"Locale\2052"
    output_folder = r"Locale\1029"
    header_path = r"Locale\Header.txt"

    os.makedirs(output_folder, exist_ok=True)

    # 修改原有的 Header.txt 邏輯
    if os.path.exists(header_path):
        try:
            with open(header_path, "r", encoding="utf-8") as f:
                header_lines = f.readlines()
                
            # 檢查是否已經存在繁體中文設定（只要有 1029 或是 繁體中文 字眼就當作已有）
            has_tc_line = any("1029," in line or "繁體中文" in line for line in header_lines)
            
            if not has_tc_line:
                new_header_lines = []
                for line in header_lines:
                    # 找到簡體中文的行，在其上方插入繁體中文的行
                    if "2052,简体中文" in line:
                        new_header_lines.append("1029,繁體中文,zhTW,zh_TW,1033,1\n")
                    new_header_lines.append(line)
                    
                with open(header_path, "w", encoding="utf-8", newline="") as f:
                    f.writelines(new_header_lines)
                print("\nHeader.txt 已成功修改並加入繁體中文選項。")
            else:
                print("\nHeader.txt 已經包含繁體中文選項，為避免故障已自動略過修改。")
                
        except Exception as e:
            print(f"\n修改 Header.txt 時發生錯誤：{e}")
    else:
        print(f"\n警告：找不到 {header_path}，無法自動修改語言列表，請手動確認。")

    # key [空白] number [空白] value [行尾]
    row_pat = re.compile(r'^([^\t\r\n]+)([\t ]+)(\d+)([\t ]+)(.*?)(\r?\n)?$')

    if not os.path.isdir(input_folder):
        print(f"找不到輸入資料夾：{input_folder}")
        return

    files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]
    if not files:
        print(f"{input_folder} 內無 .txt 檔。")
        return

    for file in files:
        input_path = os.path.join(input_folder, file)
        output_path = os.path.join(output_folder, file)

        print(f"正在處理：{file}")
        with open(input_path, "r", encoding="utf-16 LE") as fin:
            lines = fin.readlines()

        out_lines = []
        for line in lines:
            m = row_pat.match(line)
            if not m:
                out_lines.append(line)
                continue

            key, sep1, number, sep2, value, eol = m.groups()

            # 1) 簡轉繁（僅第三欄）
            new_value = converter.convert(value)

            # 2) 依取代表逐條取代（只套用在轉繁後第三欄）
            for old, new in replace_pairs:
                if old:
                    new_value = new_value.replace(old, new)

            # 3) 若 key 在覆寫表，直接覆寫第三欄（最高優先權）
            if key in key_overrides:
                new_value = key_overrides[key]

            # 4) 保留原分隔與行尾
            out_lines.append(f"{key}{sep1}{number}{sep2}{new_value}{(eol or '')}")

        with open(output_path, "w", encoding="utf-16 LE") as fout:
            fout.writelines(out_lines)

    print("\n繁體中文新增完成，結果已輸出到:", output_folder)

def switch_voice(lang="en"):
    """
    僅替換 base.txt 指定鍵的值，保留原分隔與行尾。
    lang='en' → 英文語音；lang='zh' → 中文語音；lang='ja' → 日文語音
    """
    base_path = r"Locale\1029\base.txt"
    if not os.path.exists(base_path):
        print("找不到 base.txt，請確認路徑是否正確。")
        return

    with open(base_path, "r", encoding="utf-16 LE") as f:
        lines = f.readlines()

    row_pat = re.compile(r'^([^\t\r\n]+)([\t ]+)(\d+)([\t ]+)(.*?)(\r?\n)?$')

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
    value_map_ja = {
        "ImageLogo0": "UI/Textures/dsp-logo-en",
        "ImageLogo1": "UI/Textures/dsp-logo-flat-en",
        "ImageLogo2": "UI/Textures/dsp-logo-flat-en",
        "AudioResPostfix": "-ja",
        "CutsceneBGM0": "Musics/df-cutscene-ja",
    }
    
    if lang == "en":
        value_map = value_map_en
    elif lang == "zh":
        value_map = value_map_zh
    elif lang == "ja":
        value_map = value_map_ja
    else:
        value_map = value_map_zh # 防呆預設

    out_lines = []
    for line in lines:
        m = row_pat.match(line)
        if not m:
            out_lines.append(line)
            continue

        key, sep1, number, sep2, value, eol = m.groups()
        if key in value_map:
            value = value_map[key]
        out_lines.append(f"{key}{sep1}{number}{sep2}{value}{(eol or '')}")

    with open(base_path, "w", encoding="utf-16 LE") as f:
        f.writelines(out_lines)

    if lang == "en":
        print("\nbase.txt 已修改為英文語音設定。")
    elif lang == "ja":
        print("\nbase.txt 已修改為日文語音設定。")
    else:
        print("\nbase.txt 已恢復為中文語音設定。")

if __name__ == "__main__":
    main()
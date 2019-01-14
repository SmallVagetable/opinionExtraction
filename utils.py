import re
import difflib

# 判断中文
def findChineseWord(word):
    chinese_pattern = '[\u4e00-\u9fa5]+'
    says = re.findall(chinese_pattern, word)

    if not says:
        return False

    return True

# 读取文件
def readFile(path):
    content = []
    if not path:
        return content
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            content.append(line.strip())
    return content

def similarity(opinion1, opinion2):
    return difflib.SequenceMatcher(a = opinion1, b = opinion2).quick_ratio()
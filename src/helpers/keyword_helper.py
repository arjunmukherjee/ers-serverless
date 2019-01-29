import re
from urllib.parse import unquote


def get_correct_keyword(keyword):
    keyword = re.sub('[,]', ' ', keyword)
    keyword = re.sub(' +', ' ', keyword).strip()
    return chomp(keyword)


def chomp(x):
    if x.endswith("\r\n"): return x[:-2]
    if x.endswith("\n") or x.endswith("\r"): return x[:-1]
    return x.strip()


def extract_keyword(event):
    keyword = unquote(event['pathParameters'].get('keyword'))
    return chomp(keyword)

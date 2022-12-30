import os


def _wrap_with(code):
    def inner(text, bold=False):
        c = code

        if os.environ.get("FABRIC_DISABLE_COLORS"):
            return text

        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner


ok = _wrap_with("32")  # 緑色
crit = _wrap_with("31")  # 赤色
warn = _wrap_with("33")  # 黄色
info = _wrap_with("36")  # 水色
debug = _wrap_with("35")  # 紫色

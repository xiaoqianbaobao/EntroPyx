import json
from django import template

register = template.Library()


@register.filter
def pprint(value):
    """美化输出JSON格式数据"""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)

@register.filter
def mul(value, arg):
    """乘法过滤器"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

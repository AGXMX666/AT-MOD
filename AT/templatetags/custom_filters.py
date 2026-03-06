from django import template
import json

register = template.Library()

@register.filter(name='parse_json')
def parse_json(value):
    """Parse JSON string to Python object"""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

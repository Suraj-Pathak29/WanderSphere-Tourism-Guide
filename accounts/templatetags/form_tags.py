from django import template

register = template.Library()


@register.filter(name='getitem')
def getitem(form, field_name):
    """
    Usage: {{ form|getitem:"field_name" }}
    Returns the BoundField for the given field name.
    """
    try:
        return form[field_name]
    except KeyError:
        return ''


@register.filter(name='split')
def split(value, delimiter=','):
    """
    Usage: {{ "a,b,c"|split:"," }}
    """
    return value.split(delimiter)


@register.filter(name='replace')
def replace(value, args):
    """
    Usage: {{ value|replace:"old:new" }}
    """
    try:
        old, new = args.split(':')
        return value.replace(old, new)
    except (ValueError, AttributeError):
        return value


@register.simple_tag
def interest_fields():
    """Returns list of (field_name, emoji) tuples for the interest fields."""
    return [
        ('pref_culture',   '🏛️'),
        ('pref_adventure', '🏔️'),
        ('pref_nature',    '🌿'),
        ('pref_beaches',   '🏖️'),
        ('pref_nightlife', '🌃'),
        ('pref_cuisine',   '🍜'),
        ('pref_wellness',  '🧘'),
        ('pref_urban',     '🏙️'),
        ('pref_seclusion', '🌲'),
    ]

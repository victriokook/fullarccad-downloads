import re

def checked_instances(value,count,current=()):
    if type(count) is not int or not 2<=count<=200:raise ValueError('Count must be an integer in2..200')
    if value is None:value=current
    if type(value) not in (tuple,list) or len(value)>199:raise ValueError('Use at most199 integer indices')
    if any(type(item) is not int or not 2<=item<=count for item in value):raise ValueError('Indices must be in2..count;original1 cannot be omitted')
    if len(set(value))!=len(value):raise ValueError('Duplicate omitted instance')
    return tuple(sorted(value))

def parse_instances(text,count):
    checked_instances((),count)
    if type(text) is not str or len(text)>2000:raise ValueError('Invalid omitted indices text')
    if not text.strip():return ()
    parts=[item.strip() for item in text.split(',')]
    if any(re.fullmatch(r'[1-9][0-9]{0,2}',item) is None for item in parts):raise ValueError('Use comma-separated ASCII integer indices')
    return checked_instances([int(item) for item in parts],count)

def format_instances(value,count):
    return ','.join(str(item) for item in checked_instances(value,count))

"""Codex-reviewed local-Qwen selection validator, zero-based region indices."""
def kept_indices(values,count):
    if isinstance(count,bool) or not isinstance(count,int) or not 2<=count<=200:
        raise ValueError('Expected2–200 regions')
    if isinstance(values,(str,bytes)):raise ValueError('Expected integer region indices')
    try:result=tuple(values)
    except TypeError:raise ValueError('Expected iterable region indices') from None
    if not result or len(result)>=count:raise ValueError('Keep at least one region and remove at least one')
    if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<count for v in result):
        raise ValueError('Invalid region index')
    if len(set(result))!=len(result):raise ValueError('Duplicate region index')
    return result

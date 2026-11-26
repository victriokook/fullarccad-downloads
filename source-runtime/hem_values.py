"""Reviewed local-Qwen hem input contract; dimensions are millimetres."""
import math

def validate(kind,width,opening,radius,roll_angle,include_bend,invert,thickness):
    if type(kind) is not str or kind not in ('Flat','Open','Teardrop','Rolled'):raise ValueError('Invalid hem type')
    if type(include_bend) is not bool or type(invert) is not bool:raise ValueError('Hem switches must be boolean')
    result=[]
    for v,lo,hi in zip((width,opening,radius,roll_angle,thickness),(.001,0,.001,.1,1e-7),(100000,100000,100000,359.9,10000)):
        if type(v) not in (int,float):raise ValueError('Hem dimensions require numbers')
        try:v=float(v)
        except OverflowError:raise ValueError('Hem dimension overflow') from None
        if not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Hem dimension is outside its range')
        result.append(v)
    width,opening,radius,roll_angle,thickness=result
    if thickness<=1e-7:raise ValueError('Sheet is too thin')
    if kind=='Open' and opening<.001:raise ValueError('Open hem gap must be at least .001mm')
    if kind in ('Flat','Open') and include_bend and width<=thickness+(opening/2 if kind=='Open' else 0):raise ValueError('Hem width must exceed bend width')
    if kind=='Teardrop' and width<2*(radius+thickness):raise ValueError('Teardrop width must be at least twice radius plus thickness')
    return kind,width,opening,radius,roll_angle,include_bend,invert

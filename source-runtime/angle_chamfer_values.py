"""Strict finite native chamfer distance/angle input."""
import math

def distance_angle(distance,angle):
    for value,low,high in ((distance,.001,100000),(angle,.1,89.9)):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or value<low or value>high or not math.isfinite(value):
            raise ValueError('Distance must be 0.001..100000 mm and angle 0.1..89.9 degrees.')
    return float(distance),float(angle)

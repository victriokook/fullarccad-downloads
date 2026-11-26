"""Preserve exact BRep except Checked metadata in each TShape flag record."""
import hashlib
import re
import FreeCAD as App


def normalized(text):
    lines=text.splitlines(keepends=True)
    headers=[i for i,line in enumerate(lines) if re.fullmatch(r"TShapes [0-9]+\s*",line)]
    if len(headers)!=1:raise ValueError("Unsupported topology serialization")
    start=headers[0];expected=int(lines[start].split()[1]);found=0
    for i in range(start+1,len(lines)-1):
        flag=lines[i].rstrip("\r\n")
        # A flag record is seven bits followed by the child-reference list.
        if re.fullmatch(r"[01]{7}",flag) and re.fullmatch(r"(?:[+\-iIeE][0-9]+ [0-9]+ )*\*\s*",lines[i+1]):
            lines[i]=flag[:2]+"0"+flag[3:]+lines[i][len(flag):];found+=1
    if found!=expected:raise ValueError("Unrecognized topology flag records")
    return "".join(lines)


def shape_fingerprint(value):
    shape=value.copy();shape.Placement=App.Placement()
    return hashlib.sha256(normalized(shape.exportBrepToString()).encode("utf-8")).hexdigest()


def fingerprint(source):
    return shape_fingerprint(source.Shape)

import types,math
import FreeCAD as App,Part
import model,sheetmetal_bridge
from four_ops_values import number,flag
from four_ops import element
TITLE=('スケッチ線に沿って折曲げ','Fold Along Sketch Line')
HINT=('平板の広い平面FaceN→その面を横切る単一直線スケッチ全体を選択。\n曲げは線の中央配置。1曲げ・任意の固定側反転。自動リリーフ／複数線／製造保証／形状プレビューなし。','Select broad planar FaceN of a flat plate,then a single straight sketch spanning it.\nOne centered fold,stationary side/direction flips. No automatic relief,multiple lines,manufacturing certification or geometry preview.')
DEFAULTS=dict(radius=2.,angle=90.,kfactor=.5,reverse=False,side=False)
FIELDS=[('radius','内側半径 mm','Inner Radius mm',.001,10000),('angle','角度 °','Angle degrees',.1,179.9),('kfactor','K係数','K-factor',0,1)]
FLAGS=[('reverse','曲げ方向反転','Reverse bend'),('side','固定側反転','Switch stationary side')]
def selection(s):
    if len(s)!=2 or len(s[0].SubElementNames)!=1 or s[1].SubElementNames:raise ValueError('Select plate FaceN then whole straight sketch')
    return [x.Object for x in s],[s[0].SubElementNames[0]]
def shape(s,e,o):
    sheetmetal_bridge.unavailable()

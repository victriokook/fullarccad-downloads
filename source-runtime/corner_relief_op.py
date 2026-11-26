import types
import Part,model,sheetmetal_bridge
from four_ops_values import number
from four_ops import element
TITLE=('コーナーリリーフ','Corner Relief')
HINT=('同じ板金ソリッドの2つの直線曲げ境界EdgeNを選択。\n円形・寸法指定、K係数。自動コーナー検出／3曲げ／カスタム輪郭／形状プレビューなし。','Select two straight bend boundary EdgeN on one sheet solid.\nCircular relief with explicit size and K-factor. No automatic corner search,three-bend corners,custom profile or geometry preview.')
DEFAULTS=dict(size=4.,kfactor=.5);FIELDS=[('size','半径 mm','Radius mm',.001,10000),('kfactor','K係数','K-factor',0,1)];FLAGS=[]
def selection(s):
    if len(s)!=1 or len(s[0].SubElementNames)!=2:raise ValueError('Select two bend boundary edges on one solid')
    return [s[0].Object],list(s[0].SubElementNames)
def shape(s,e,o):
    sheetmetal_bridge.unavailable()

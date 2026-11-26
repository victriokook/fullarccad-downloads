import Part,model,sheetmetal_bridge
from four_ops import element
from four_ops_values import number
TITLE=('継ぎ目の隙間を作成','Create Seam Gap')
HINT=('一定断面の中空押出ボディの直線コーナーEdgeNを1つ選択。\n両端の開口・単一ソリッドを検証。入力はnative切除距離で、最小実隙間幅とは異なります。\n任意面の裂け目／全体自動検出／形状プレビューなし。','Select one straight corner EdgeN of a constant-section hollow extrusion.\nBoth ends must open and result must remain one solid. Input is native cut distance,not minimum physical gap width.\nNo arbitrary-face rip,automatic seam detection or geometry preview.')
DEFAULTS=dict(gap=2.);FIELDS=[('gap','native切除距離 mm','Native cut distance mm',.001,1000)];FLAGS=[]
def selection(s):
    if len(s)!=1 or len(s[0].SubElementNames)!=1:raise ValueError('Select one straight seam corner EdgeN')
    return [s[0].Object],list(s[0].SubElementNames)
def shape(s,e,o):
    sheetmetal_bridge.unavailable()

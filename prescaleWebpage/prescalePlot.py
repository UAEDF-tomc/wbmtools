#
# Everything to make the prescale plot
# Requires plotly installed
# Returns content to be included in html
#
from helpers import getIntLumi
import plotly
import plotly.graph_objs as go
def prescalePlot(hltPath, prescales, year, goodLumis, puData, runsInfo):

  def getXaxis(maxLumi, year):
    return {
        "title": "lumi for " + year + " (fb<sup>-1</sup>)",
        "titlefont": {"color": "#673ab7"},
        "rangemode": "nonnegative",
        "range": [0., maxLumi], 
        "rangeslider": {"autorange": True, "bgcolor" : "#f2f8f9"},
        "type": "linear",
        "zeroline": False,
        "showgrid": False,
      }

  def getYaxis():
    return {
        "title": "prescale",
        "anchor": "x", 
        "autorange": True,
        "rangemode": "nonnegative",
        "linecolor": "#673ab7", 
        "side": "left", 
        "tickfont": {"color": "#673ab7"}, 
        "tickmode": "auto", 
        "ticks": "", 
        "titlefont": {"color": "#673ab7"}, 
        "type": "linear", 
        "showgrid": False,
        "zeroline": False
      }

  # Returns the shapes and annotations to indicate the trigger menus
  def getMenus(runsInfo, lumiSinceStart, maxLumi, goodLumis):
    menus, runs, intLumi = [], [], []
    for r in sorted(runsInfo.keys()):
      if r not in goodLumis: continue
      maxR = r
      menu = runsInfo[r]['hlt_menu'].split('/HLT')[0].split('/')[-1]
      if not len(menus) or menu != menus[-1]: 
        menus.append(menu)
        runs.append(r)
        intLumi.append(lumiSinceStart[(int(r), goodLumis[r][0][0])])
    runs.append(maxR)
    intLumi.append(maxLumi)

    shapes, annotations = [], []
    colors = ['#ffdfdf', '#e0e1ff', '#fff4e0', '#ddffe5', '#e2e1ff']
    for i, menu in enumerate(menus):
      shapes.append({
          "fillcolor": colors[len(shapes)%len(colors)],
          "layer": "below",
          "opacity": 0.5,
          "line": {"width": 0},
          "type": "rect", 
          "x0": intLumi[i],
          "x1": intLumi[i+1], 
          "xref": "x", 
          "y0": 0, 
          "y1": 1,
          "yref": "paper"})
      annotations.append({
          "text": menu,
          "textangle": 45,
          "x": (intLumi[i]+(intLumi[i+1]-intLumi[i])/2.),
          "xref": "x", 
          "y": 1,
          "font": {"size" : 9},
          "arrowwidth" : 0.3,
          "arrowsize" : 2.5,
          "hovertext" : ('HLT menu ' + menu + ' active in runs ' + str(runs[i]) + '-' + str(int(runs[i+1])-1)),
          "yref": "paper"})
    return shapes, annotations


  # Construct arrays with the lumi, prescale and run label at each change
  def constructScatter(name, prescales, lumiSinceStart, maxLumi, hltOff):
    changeOfPrescale = []

    for p, compactList in prescales.iteritems():
      try:    p = int(p)
      except: p = None
      for run, lumis in compactList.iteritems():
        for lumiRange in lumis:
          try:    changeOfPrescale.append((lumiSinceStart[(int(run), int(lumiRange[0]))], p, str(run)+ ':' + str(lumiRange[0]) + ' --> ' + (('prescale ' + str(p)) if p is not None else 'seed off')))
          except: pass # Temporary for 2018 lumis which are not in pu json

    for compactList in hltOff: # Set to None when hlt path was off
      for run, lumis in compactList.iteritems():
        for lumiRange in lumis:
          try:    changeOfPrescale.append((lumiSinceStart[(int(run), int(lumiRange[0]))], None, str(run)+ ':' + str(lumiRange[0]) + ' --> hlt path off'))
          except: pass # Temporary for 2018 lumis which are not in pu json

    changeOfPrescale.sort(key=lambda k : k[0])
    x, y, text = zip(*changeOfPrescale)
    x    = sum([[x[i], x[i+1]] for i in range(len(x)-1)], []) + [x[-1], maxLumi]
    y    = sum([[i, i] for i in y], [])
    text = sum([[i, ''] for i in text], [])
    scat = go.Scatter(x=x, y=y, name=name, yaxis= "y", text=text)
    scat.update({"hoverinfo": "name+x+text",
                 "line": {"width": 1. if 'HLT' in name else 0.5}, 
                 "marker": {"size": 8},
                 "mode": "lines",
                 "showlegend": True})
    return scat

  hlt            = [i for i in prescales.keys() if 'HLT' in i][0]
  lumiSinceStart = getIntLumi(goodLumis, puData, getDict=True)
  maxLumi        = max(lumiSinceStart.values())
  hltOff         = [l for p, l in prescales[hlt].iteritems() if p=='NotExisting' or int(p)==0]
  data           = [constructScatter(i, prescales[i], lumiSinceStart, maxLumi, hltOff) for i in sorted(prescales.keys())]
  maxPrescale    = 10
  shapes, annotations = getMenus(runsInfo, lumiSinceStart, maxLumi, goodLumis)

  layout = {
    "title": 'Prescales for seeds used in ' + hlt + ' (' + year + ')',
    "dragmode": "zoom", 
    "hovermode": "x",
    "hoverlabel": {"font": {"size" : 7}, "namelength" : -1},
    "legend": {"traceorder": "normal", "font": {"size" : 8}, "tracegroupgap" : 5},
    "margin": {"t": 100, "b": 100}, 
    "shapes": shapes,
    "annotations": annotations,
    "xaxis": getXaxis(maxLumi, year), 
    "yaxis": getYaxis(),
  }
  fig = go.Figure(data=data, layout=layout)

  div  = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
  div += plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')
  return div

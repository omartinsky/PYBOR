import pylab
import IPython.display

def display_dataframes(dataframes, nColumns=3):
    table = "<table style='width:100%; border:0px'>{content}</table>"
    row = "<tr style='border:0px'>{content}</tr>"
    cell = "<td style='width:{width}%;vertical-align:top;border:0px'>{{content}}</td>"
    cell = cell.format(width=100 / nColumns)

    cells = [cell.format(content=df.to_html()) for df in dataframes]
    cells += (nColumns - (len(dataframes) % nColumns)) * [cell.format(content="")] # pad
    rows = [row.format(content="".join(cells[i:i + nColumns])) for i in range(0, len(cells), nColumns)]
    IPython.display.display(IPython.display.HTML(table.format(content="".join(rows))))

def figsize(w, h):
	pylab.rcParams['figure.figsize'] = w,h

def linestyle(style, reset_color_counter=True):
    pylab.rcParams['lines.linestyle'] = style
    if reset_color_counter:
        pylab.gca().set_prop_cycle(None)  # Reset Colors Counter
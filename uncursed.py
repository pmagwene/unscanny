import curses
import curses.panel as panel

def centered_xcoord(win, s):
    nrows, ncols = win.getmaxyx()
    if isinstance(s, int):
        maxlen = s
    else:
        maxlen = max([len(i) for i in str(s).splitlines()])
    return (ncols // 2) - (maxlen // 2)

def centered_ycoord(win, s):
    nrows, ncols = win.getmaxyx()
    if isinstance(s, int):
        nlines = s
    else:
        nlines = len(str(s).splitlines())
    return (nrows // 2) - (nlines // 2)
    
def add_multiline_str(win, y, x, s):
    lines = s.splitlines()
    for i, line in enumerate(lines):
        win.addstr(y + i, x, line)
    
def set_status_bar(win, s, loc="bottom"):
    nrows, ncols = win.getmaxyx()
    y = 0 if (loc == "top") else (nrows - 1)
    win.move(y, 0)
    win.clrtoeol()
    win.addstr(y, 0, s)


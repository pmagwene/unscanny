import string
import curses
import curses.panel as panel

def max_line_len(s):
    return max([len(i) for i in s.splitlines()])

def centered_xcoord(win, s):
    nrows, ncols = win.getmaxyx()
    if isinstance(s, int):
        maxlen = s
    else:
        maxline = max_line_len(s)
    return (ncols // 2) - (maxlen // 2)

def centered_ycoord(win, s):
    nrows, ncols = win.getmaxyx()
    if isinstance(s, int):
        nlines = s
    else:
        nlines = len(str(s).splitlines())
    return (nrows // 2) - (nlines // 2)
    
def adjust_lines(s, func=string.ljust):
    maxlen = max_line_len(s)
    adj_lines = [func(i, maxlen) for i in s.splitlines()]
    return "\n".join(adj_lines)

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

def new_text_win(s, padding = 1, just = None):
    nlines = len(s.splitlines()) + 2 * padding
    ncols = max_line_len(s) + 2 * padding
    win = curses.newwin(nlines, ncols)
    if just is not None:
        s = adjust_lines(s, just)
    add_multiline_str(win, padding, padding, s)
    return win 

def setup_screen(screen, nonblocking=True):
    screen.clear()
    screen.nodelay(int(nonblocking))
    curses.curs_set(0)
    
def test(screen, s, just=None):
    setup_screen(screen, nonblocking=True)
    win = new_text_panel(s, just = just)
    h, w = win.getmaxyx()
    y, x = centered_ycoord(screen, h), centered_xcoord(screen, w)
    win.mvwin(y,x)

    set_status_bar(screen, "Push 'q' to quit")
    screen.refresh()
    win.refresh()

    # loop until receive 'q'
    while True:
        c = screen.getch()
        if c in (ord('q'), ord('Q')):
            break
        
    

import requests
import curses

def getSubpages(page):
	response = requests.get(f'https://www.svt.se/text-tv/api/{page}')
	json = response.json()
	status = json['status']

	try:
		data = json['data']
		prevPage = data['prevPage']
		nextPage = data['nextPage']
		subPages = data['subPages']
		return (status, subPages, prevPage, nextPage)
	except KeyError:
		return (status, [], -1, -1)

def parseText(altText):
	lines = list(filter(lambda line : line != '', altText.split('\n')))
	width = max(list(map(lambda line : len(line), lines)))
	lines = list(map(lambda line : line.strip().ljust(width + 2).rjust(width + 4), lines))

	groups = []
	group = []

	footer = lines[-2:-1]
	lines = lines[:-1]

	for line in lines:
		if all(c == ' ' for c in line):
			if group != []:
				groups.append(group)
				group = []
		else:
			group.append(line)
		
	if len(groups) > 0:
		header = groups[0]
		groups = groups[1:]
	else:
		header = []

	return (header, footer, groups)

def renderText(stdscr, subpage):
	y = 0
	x = 0

	(header, footer, groups) = parseText(subpage['altText'])

	if (len(header) > 0):
		stdscr.addstr(y, x, header[0])
		y += 1
	if (len(header) > 1):
		stdscr.addstr(y, x, header[1], curses.color_pair(1))
		y += 1
	y += 1
		

	for i, group in enumerate(groups):
		for line in group:
			if i == 0 and len(group) == 1:
				stdscr.addstr(y, x, line, curses.A_STANDOUT)
			elif i % 2 == 0:
				stdscr.addstr(y, x, line, curses.color_pair(2))
			else:
				stdscr.addstr(y, x, line)
			y += 1
		y += 1

	if (len(footer) > 0):
		stdscr.addstr(curses.LINES - 1, x, footer[0], curses.color_pair(1))

def main(stdscr):
	curses.noecho()
	curses.cbreak()
	curses.curs_set(0)
	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
	curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

	currentPage = 100
	currentSubpage = 0
	oldPage = currentPage
	(status, subpages, prevPage, nextPage) = getSubpages(currentPage)

	running = True
	while running:
		if currentPage != oldPage:
			(status, newSubpages, newPrevPage, newNextPage) = getSubpages(currentPage)
			if status == 'success':
				subpages = newSubpages
				prevPage = newPrevPage
				nextPage = newNextPage

				if currentPage < oldPage:
					currentSubpage = len(subpages) - 1
					stdscr.addstr(str(currentSubpage))
				else:
					currentSubpage = 0
				oldPage = currentPage
			else:
				currentPage = oldPage

		stdscr.clear()

		renderText(stdscr, subpages[currentSubpage])

		stdscr.refresh()

		c = stdscr.getch()
		if c == ord('q'):
			running = False

		elif c == ord('p') or c == ord('h'):
			if len(subpages) > 1 and 0 < currentSubpage:
				currentSubpage -= 1
			elif prevPage != '':
				currentPage = int(prevPage)

		elif c == ord('n') or c == ord('l'):
			if len(subpages) > 1 and currentSubpage < len(subpages) - 1:
				currentSubpage += 1
			elif nextPage != '':
				currentPage = int(nextPage)
		elif c == ord(':'):
			curses.echo()
			stdscr.addstr(0, 2, '   ')
			s = stdscr.getstr(0, 2, 3)
			currentPage = int(s)
			curses.noecho()

def run():
	curses.wrapper(main)

if __name__ == '__main__':
	run()
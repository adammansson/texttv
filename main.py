import requests
import base64
from PIL import Image
import io
import pygame
import re
import argparse
import curses

def parseImage(data):
	gifBytes = base64.b64decode(data)
	image = Image.open(io.BytesIO(gifBytes)).convert('RGBA')
	return pygame.image.fromstring(image.tobytes(), image.size, image.mode)

def parseMap(data):
	pattern = r'COORDS="([\d,]+)" HREF="(\d+)"'
	areas = []
	for coords, href in re.findall(pattern, data):
		x1, y1, x2, y2 = map(int, coords.split(','))
		areas.append(((x1, y1, x2, y2), href))
	return areas

def getPage(page):
	response = requests.get(f'https://www.svt.se/text-tv/api/{page}')
	data = response.json()['data']
	prevPage = data['prevPage']
	nextPage = data['nextPage']
	subPage = data['subPages'][0]

	return(prevPage, nextPage, subPage)

def getGraphical(page):
	(prevPage, nextPage, subPage) = getPage(page)
	gifAsBase64 = subPage['gifAsBase64']
	imageMap = subPage['imageMap']

	return	(
		prevPage,
		nextPage,
		parseImage(gifAsBase64),
		parseMap(imageMap),
		)

def getTerminal(page):
	(prevPage, nextPage, subPage) = getPage(page)
	altText = subPage['altText']

	return	(
		prevPage,
		nextPage,
		altText
		)

def viewGraphical():
	print('GRAPHICAL')

	pygame.init()

	oldPage = 100
	currentPage = oldPage
	(prevPage, nextPage, background, areas) = getGraphical(currentPage)
	inRect = False

	screen = pygame.display.set_mode(background.get_size())
	pygame.display.set_caption('TextTV')

	running = True
	while running:
		if currentPage != oldPage:
			print('UPDATE')
			oldPage = currentPage
			(prevPage, nextPage, background, areas) = getGraphical(currentPage)

		if inRect:
			pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
		else:
			pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				print('QUIT')
				running = False
			
			elif event.type == pygame.MOUSEMOTION:
				x, y = event.pos
				inRect = False
				for (x1, y1, x2, y2), newPage in areas:
					if x1 <= x <= x2 and y1 <= y <= y2:
						inRect = True

			elif event.type == pygame.MOUSEBUTTONDOWN:
				x, y = event.pos
				for (x1, y1, x2, y2), newPage in areas:
					if x1 <= x <= x2 and y1 <= y <= y2:
						currentPage = int(newPage)

			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					print('QUIT')
					running = False

				elif event.key == pygame.K_LEFT:
					if prevPage != '':
						currentPage = prevPage

				elif event.key == pygame.K_RIGHT:
					if nextPage != '':
						currentPage = nextPage

		screen.blit(background, (0, 0))
		pygame.display.flip()

	pygame.quit()

def viewTerminal():
	print('TERMINAL')

	currentPage = 100
	oldPage = currentPage
	(prevPage, nextPage, altText) = getTerminal(currentPage)

	running = True
	while running:
		if currentPage != oldPage:
			oldPage = currentPage
			(prevPage, nextPage, altText) = getTerminal(currentPage)

		print(altText)
		print(f'{prevPage} < {currentPage} > {nextPage}')

		userInput = input()
		if userInput == 'q':
			print('QUIT')
			running = False
		elif userInput == 'p':
			if prevPage != '':
				currentPage = prevPage
		elif userInput == 'n':
			if nextPage != '':
				currentPage = nextPage

def viewCurses():
	print('CURSES')

	stdscr = curses.initscr()
	curses.noecho()
	curses.cbreak()

	currentPage = 100
	oldPage = currentPage
	(prevPage, nextPage, altText) = getTerminal(currentPage)

	running = True
	while running:
		if currentPage != oldPage:
			oldPage = currentPage
			(prevPage, nextPage, altText) = getTerminal(currentPage)

		stdscr.clear()
		stdscr.addstr(0, 0, altText)
		stdscr.addstr(curses.LINES - 1, 0, f'{prevPage} < {currentPage} > {nextPage}')

		c = stdscr.getch()
		if c == ord('q'):
			running = False

		elif c == ord('p'):
			if prevPage != '':
				currentPage = prevPage

		elif c == ord('n'):
			if nextPage != '':
				currentPage = nextPage

	curses.endwin()

def run():
	parser = argparse.ArgumentParser(
					prog='TextTV',
					description='TextTV viewer in Python'
					)

	parser.add_argument(
				'mode',
				choices=['graphical', 'terminal', 'curses'],
				nargs='?',
				default='terminal'
			)
	args = parser.parse_args()

	if args.mode == 'terminal':
		viewTerminal()
	elif args.mode == 'curses':
		viewCurses()
	else:
		viewGraphical()

if __name__ == '__main__':
	run()
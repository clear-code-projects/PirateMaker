import pygame
from pygame.math import Vector2 as vector
from settings import *
from support import *

from pygame.image import load

from editor import Editor
from level import Level

class Main:
	def __init__(self):
		pygame.init()
		self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		self.clock = pygame.time.Clock()
		self.imports()

		self.editor_active = True
		self.transition = Transition(self.toggle)
		self.editor = Editor(self.land_tiles, self.switch)

		# cursor 
		surf = load('../graphics/cursors/mouse.png').convert_alpha()
		cursor = pygame.cursors.Cursor((0,0), surf)
		pygame.mouse.set_cursor(cursor)

	def imports(self):
		# terrain
		self.land_tiles = import_folder_dict('../graphics/terrain/land')
		self.water_bottom = load('../graphics/terrain/water/water_bottom.png').convert_alpha()
		self.water_top_animation = import_folder('../graphics/terrain/water/animation')

		# coins
		self.gold = import_folder('../graphics/items/gold')
		self.silver = import_folder('../graphics/items/silver')
		self.diamond = import_folder('../graphics/items/diamond')
		self.particle = import_folder('../graphics/items/particle')

	def toggle(self):
		self.editor_active = not self.editor_active

	def switch(self, grid = None):
		self.transition.active = True
		if grid:
			self.level = Level(grid, self.switch,{
				'land': self.land_tiles,
				'water bottom': self.water_bottom,
				'water top': self.water_top_animation,
				'gold': self.gold,
				'silver': self.silver,
				'diamond': self.diamond,
				'particle': self.particle
				})

	def run(self):
		while True:
			dt = self.clock.tick() / 1000
			
			if self.editor_active:
				self.editor.run(dt)
			else:
				self.level.run(dt)
			self.transition.display(dt)
			pygame.display.update()


class Transition:
	def __init__(self, toggle):
		self.display_surface = pygame.display.get_surface()
		self.toggle = toggle
		self.active = False

		self.border_width = 0
		self.direction = 1
		self.center = (WINDOW_WIDTH /2, WINDOW_HEIGHT / 2)
		self.radius = vector(self.center).magnitude()
		self.threshold = self.radius + 100

	def display(self, dt):
		if self.active:
			self.border_width += 1000 * dt * self.direction
			if self.border_width >= self.threshold:
				self.direction = -1
				self.toggle()
			
			if self.border_width < 0:
				self.active = False
				self.border_width = 0
				self.direction = 1
			pygame.draw.circle(self.display_surface, 'black',self.center, self.radius, int(self.border_width))

if __name__ == '__main__':
	main = Main()
	main.run() 
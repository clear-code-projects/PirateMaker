import pygame, sys 
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_pos
from pygame.image import load

from settings import *
from support import *

from menu import Menu

class Editor:
	def __init__(self, land_tiles):
		
		# main setup 
		self.display_surface = pygame.display.get_surface()
		self.canvas_data = {}

		# imports 
		self.land_tiles = land_tiles
		self.imports()

		# navigation
		self.origin = vector()
		self.pan_active = False
		self.pan_offset = vector()

		# support lines 
		self.support_line_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		self.support_line_surf.set_colorkey('green')
		self.support_line_surf.set_alpha(30)

		# selection
		self.selection_index = 2
		self.last_selected_cell = None

		# menu 
		self.menu = Menu()


	# support
	def get_current_cell(self):
		distance_to_origin = vector(mouse_pos()) - self.origin

		if distance_to_origin.x > 0:
			col = int(distance_to_origin.x / TILE_SIZE)
		else:
			col = int(distance_to_origin.x / TILE_SIZE) - 1

		if distance_to_origin.y > 0:
			row = int(distance_to_origin.y / TILE_SIZE)
		else:
			row = int(distance_to_origin.y / TILE_SIZE) - 1

		return col, row

	def check_neighbors(self, cell_pos):

		# create a local cluster
		cluster_size = 3
		local_cluster = [
			(cell_pos[0] + col - int(cluster_size / 2), cell_pos[1] + row - int(cluster_size / 2)) 
			for col in range(cluster_size) 
			for row in range(cluster_size)]

		# check neighbors
		for cell in local_cluster:
			if cell in self.canvas_data:
				self.canvas_data[cell].terrain_neighbors = []
				self.canvas_data[cell].water_on_top = False
				for name, side in NEIGHBOR_DIRECTIONS.items():
					neighbor_cell = (cell[0] + side[0],cell[1] + side[1])

					if neighbor_cell in self.canvas_data:
					# water top neighbor
						if self.canvas_data[neighbor_cell].has_water and self.canvas_data[cell].has_water and name == 'A':
							self.canvas_data[cell].water_on_top = True

					# terrain neighbors
						if self.canvas_data[neighbor_cell].has_terrain:
							self.canvas_data[cell].terrain_neighbors.append(name)

	def imports(self):
		self.water_bottom = load('../graphics/terrain/water/water_bottom.png')

		# animations
		self.animations = {}
		for key, value in EDITOR_DATA.items():
			if value['graphics']:
				graphics = import_folder(value['graphics'])
				self.animations[key] = {
					'frame index': 0,
					'frames': graphics,
					'length': len(graphics)
				}

	def animation_update(self, dt):
		for value in self.animations.values():
			value['frame index'] += ANIMATION_SPEED * dt
			if value['frame index'] >= value['length']:
				value['frame index'] = 0

	# input
	def event_loop(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			self.pan_input(event)
			self.selection_hotkeys(event)
			self.menu_click(event)
			self.canvas_add()

	def pan_input(self, event):

		# middle mouse button pressed / released 
		if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
			self.pan_active = True
			self.pan_offset = vector(mouse_pos()) - self.origin

		if not mouse_buttons()[1]:
			self.pan_active = False

		# mouse wheel 
		if event.type == pygame.MOUSEWHEEL:
			if pygame.key.get_pressed()[pygame.K_LCTRL]:
				self.origin.y -= event.y * 50
			else:
				self.origin.x -= event.y * 50


		# panning update
		if self.pan_active:
			self.origin = vector(mouse_pos()) - self.pan_offset

	def selection_hotkeys(self, event):
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RIGHT:
				self.selection_index += 1
			if event.key == pygame.K_LEFT:
				self.selection_index -= 1
		self.selection_index = max(2,min(self.selection_index, 18))

	def menu_click(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(mouse_pos()):
			self.selection_index = self.menu.click(mouse_pos(), mouse_buttons())

	def canvas_add(self):
		if mouse_buttons()[0] and not self.menu.rect.collidepoint(mouse_pos()):
			current_cell = self.get_current_cell()

			if current_cell != self.last_selected_cell:

				if current_cell in self.canvas_data:
					self.canvas_data[current_cell].add_id(self.selection_index)
				else:
					self.canvas_data[current_cell] = CanvasTile(self.selection_index)
		
				self.check_neighbors(current_cell)
				self.last_selected_cell = current_cell


	# drawing 
	def draw_tile_lines(self):
		cols = WINDOW_WIDTH // TILE_SIZE
		rows = WINDOW_HEIGHT// TILE_SIZE

		origin_offset = vector(
			x = self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
			y = self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE)

		self.support_line_surf.fill('green')

		for col in range(cols + 1):
			x = origin_offset.x + col * TILE_SIZE
			pygame.draw.line(self.support_line_surf,LINE_COLOR, (x,0), (x,WINDOW_HEIGHT))

		for row in range(rows + 1):
			y = origin_offset.y + row * TILE_SIZE
			pygame.draw.line(self.support_line_surf,LINE_COLOR, (0,y), (WINDOW_WIDTH,y))

		self.display_surface.blit(self.support_line_surf,(0,0))

	def draw_level(self):
		for cell_pos, tile in self.canvas_data.items():
			pos = self.origin + vector(cell_pos) * TILE_SIZE

			# water
			if tile.has_water:
				if tile.water_on_top:
					self.display_surface.blit(self.water_bottom, pos)
				else:
					frames = self.animations[3]['frames']
					index  = int(self.animations[3]['frame index'])
					surf = frames[index]
					self.display_surface.blit(surf, pos)

			if tile.has_terrain:
				terrain_string = ''.join(tile.terrain_neighbors)
				terrain_style = terrain_string if terrain_string in self.land_tiles else 'X'
				self.display_surface.blit(self.land_tiles[terrain_style], pos)

			# coins
			if tile.coin:
				frames = self.animations[tile.coin]['frames']
				index = int(self.animations[tile.coin]['frame index'])
				surf = frames[index]
				rect = surf.get_rect(center = (pos[0] + TILE_SIZE // 2,pos[1]+ TILE_SIZE // 2))
				self.display_surface.blit(surf, rect)

			# enemies
			if tile.enemy:
				frames = self.animations[tile.enemy]['frames']
				index = int(self.animations[tile.enemy]['frame index'])
				surf = frames[index]
				rect = surf.get_rect(midbottom = (pos[0] + TILE_SIZE // 2,pos[1]+ TILE_SIZE))
				self.display_surface.blit(surf, rect)


	# update
	def run(self, dt):
		self.event_loop()

		# updating
		self.animation_update(dt)

		# drawing
		self.display_surface.fill('gray')
		self.draw_level()
		self.draw_tile_lines()
		pygame.draw.circle(self.display_surface, 'red', self.origin, 10)
		self.menu.display(self.selection_index)

class CanvasTile:
	def __init__(self, tile_id):

		# terrain
		self.has_terrain = False
		self.terrain_neighbors = []

		# water
		self.has_water = False
		self.water_on_top = False

		# coin
		self.coin = None

		# enemy
		self.enemy = None

		# objects
		self.objects = []

		self.add_id(tile_id)

	def add_id(self, tile_id):
		options = {key: value['style'] for key, value in EDITOR_DATA.items()}
		match options[tile_id]:
			case 'terrain': self.has_terrain = True
			case 'water': self.has_water = True
			case 'coin': self.coin = tile_id
			case 'enemy': self.enemy = tile_id

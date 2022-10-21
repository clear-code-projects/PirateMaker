import pygame, sys 
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_pos
from pygame.image import load

from settings import *
from support import *

from menu import Menu
from timer import Timer

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

		# objects
		self.canvas_objects = pygame.sprite.Group()
		self.object_drag_active = False
		self.object_timer = Timer(400)

		# Player
		CanvasObject(
			pos = (200, WINDOW_HEIGHT / 2), 
			frames = self.animations[0]['frames'],
			tile_id =  0, 
			origin = self.origin, 
			group = self.canvas_objects)

		# sky
		self.sky_handle = CanvasObject(
			pos = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2),
			frames = [self.sky_handle_surf],
			tile_id = 1,
			origin = self.origin,
			group = self.canvas_objects)


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
		self.water_bottom = load('../graphics/terrain/water/water_bottom.png').convert_alpha()
		self.sky_handle_surf = load('../graphics/cursors/handle.png').convert_alpha()

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

		# preview
		self.preview_surfs = {key: load(value['preview']) for key, value in EDITOR_DATA.items() if value['preview']}

	def animation_update(self, dt):
		for value in self.animations.values():
			value['frame index'] += ANIMATION_SPEED * dt
			if value['frame index'] >= value['length']:
				value['frame index'] = 0

	def mouse_on_object(self):
		for sprite in self.canvas_objects:
			if sprite.rect.collidepoint(mouse_pos()):
				return sprite


	# input
	def event_loop(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			
			self.pan_input(event)
			self.selection_hotkeys(event)
			self.menu_click(event)

			self.object_drag(event)
			
			self.canvas_add()
			self.canvas_remove()

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

			for sprite in self.canvas_objects:
				sprite.pan_pos(self.origin)

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
		if mouse_buttons()[0] and not self.menu.rect.collidepoint(mouse_pos()) and not self.object_drag_active:
			current_cell = self.get_current_cell()
			if EDITOR_DATA[self.selection_index]['type'] == 'tile':

				if current_cell != self.last_selected_cell:

					if current_cell in self.canvas_data:
						self.canvas_data[current_cell].add_id(self.selection_index)
					else:
						self.canvas_data[current_cell] = CanvasTile(self.selection_index)
			
					self.check_neighbors(current_cell)
					self.last_selected_cell = current_cell
			else: # object
				if not self.object_timer.active:
					CanvasObject(
						pos = mouse_pos(),
						frames = self.animations[self.selection_index]['frames'],
						tile_id = self.selection_index,
						origin = self.origin,
						group = self.canvas_objects)
					self.object_timer.activate()

	def canvas_remove(self):
		if mouse_buttons()[2] and not self.menu.rect.collidepoint(mouse_pos()):

			# delete object
			selected_object = self.mouse_on_object()
			if selected_object:
				if EDITOR_DATA[selected_object.tile_id]['style'] not in ('player', 'sky'):
					selected_object.kill()

			# delete tiles
			if self.canvas_data:
				current_cell = self.get_current_cell()
				if current_cell in self.canvas_data:
					self.canvas_data[current_cell].remove_id(self.selection_index)

					if self.canvas_data[current_cell].is_empty:
						del self.canvas_data[current_cell]
					self.check_neighbors(current_cell)

	def object_drag(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
			for sprite in self.canvas_objects:
				if sprite.rect.collidepoint(event.pos):
					sprite.start_drag()
					self.object_drag_active = True

		if event.type == pygame.MOUSEBUTTONUP and self.object_drag_active:
			for sprite in self.canvas_objects:
				if sprite.selected:
					sprite.drag_end(self.origin)
					self.object_drag_active = False


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
		self.canvas_objects.draw(self.display_surface)

	def preview(self):
		selected_object = self.mouse_on_object()
		if not self.menu.rect.collidepoint(mouse_pos()):
			if selected_object:
				rect = selected_object.rect.inflate(10,10)
				color = 'black'
				width = 3
				size = 15

				# topleft
				pygame.draw.lines(self.display_surface, color, False, ((rect.left,rect.top + size), rect.topleft, (rect.left + size,rect.top)), width)
				#topright
				pygame.draw.lines(self.display_surface, color, False, ((rect.right - size,rect.top), rect.topright, (rect.right,rect.top + size)), width)
				# bottomright
				pygame.draw.lines(self.display_surface, color, False, ((rect.right - size, rect.bottom), rect.bottomright, (rect.right,rect.bottom - size)), width)
				# bottomleft
				pygame.draw.lines(self.display_surface, color, False, ((rect.left,rect.bottom - size), rect.bottomleft, (rect.left + size,rect.bottom)), width)
				
			else:
				type_dict = {key: value['type'] for key, value in EDITOR_DATA.items()}
				surf = self.preview_surfs[self.selection_index].copy()
				surf.set_alpha(200)
				
				# tile 
				if type_dict[self.selection_index] == 'tile':
					current_cell = self.get_current_cell()
					rect = surf.get_rect(topleft = self.origin + vector(current_cell) * TILE_SIZE)
				# object 
				else:
					rect = surf.get_rect(center = mouse_pos())
				self.display_surface.blit(surf, rect)


	# update
	def run(self, dt):
		self.event_loop()

		# updating
		self.animation_update(dt)
		self.canvas_objects.update(dt)
		self.object_timer.update()

		# drawing
		self.display_surface.fill('gray')
		self.draw_level()
		self.draw_tile_lines()
		pygame.draw.circle(self.display_surface, 'red', self.origin, 10)
		self.preview()
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
		self.is_empty = False

	def add_id(self, tile_id):
		options = {key: value['style'] for key, value in EDITOR_DATA.items()}
		match options[tile_id]:
			case 'terrain': self.has_terrain = True
			case 'water': self.has_water = True
			case 'coin': self.coin = tile_id
			case 'enemy': self.enemy = tile_id

	def remove_id(self, tile_id):
		options = {key: value['style'] for key, value in EDITOR_DATA.items()}
		match options[tile_id]:
			case 'terrain': self.has_terrain = False
			case 'water': self.has_water = False
			case 'coin': self.coin = None
			case 'enemy': self.enemy = None
		self.check_content()

	def check_content(self):
		if not self.has_terrain and not self.has_water and not self.coin and not self.enemy:
			self.is_empty = True

class CanvasObject(pygame.sprite.Sprite):
	def __init__(self, pos, frames, tile_id, origin, group):
		super().__init__(group)
		self.tile_id = tile_id

		# animation
		self.frames = frames
		self.frame_index = 0

		self.image = self.frames[self.frame_index]
		self.rect = self.image.get_rect(center = pos)

		# movement
		self.distance_to_origin = vector(self.rect.topleft) - origin
		self.selected = False
		self.mouse_offset = vector()

	def start_drag(self):
		self.selected = True
		self.mouse_offset = vector(mouse_pos()) - vector(self.rect.topleft)

	def drag(self):
		if self.selected:
			self.rect.topleft = mouse_pos() - self.mouse_offset

	def drag_end(self, origin):
		self.selected = False
		self.distance_to_origin = vector(self.rect.topleft) - origin

	def animate(self, dt):
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index = 0 if self.frame_index >= len(self.frames) else self.frame_index
		self.image = self.frames[int(self.frame_index)]
		self.rect = self.image.get_rect(midbottom = self.rect.midbottom)

	def pan_pos(self, origin):
		self.rect.topleft = origin + self.distance_to_origin

	def update(self, dt):
		self.animate(dt)
		self.drag()
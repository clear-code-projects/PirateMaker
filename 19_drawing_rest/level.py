import pygame, sys 
from pygame.math import Vector2 as vector

from settings import *
from support import *

from sprites import Generic, Animated, Particle, Coin, Player, Spikes, Tooth, Shell

class Level:
	def __init__(self, grid, switch, asset_dict):
		self.display_surface = pygame.display.get_surface()
		self.switch = switch

		# groups 
		self.all_sprites = pygame.sprite.Group()
		self.coin_sprites = pygame.sprite.Group()
		self.damage_sprites = pygame.sprite.Group()

		self.build_level(grid, asset_dict)

		# additional stuff
		self.particle_surfs = asset_dict['particle']

	def build_level(self, grid, asset_dict):
		for layer_name, layer in grid.items():
			for pos, data in layer.items():
				if layer_name == 'terrain':
					Generic(pos, asset_dict['land'][data], self.all_sprites)
				if layer_name == 'water':
					if data == 'top':
						Animated(asset_dict['water top'], pos, self.all_sprites)
					else:
						Generic(pos, asset_dict['water bottom'], self.all_sprites)

				match data:
					case 0: self.player = Player(pos, self.all_sprites)
					
					# coins
					case 4: Coin('gold', asset_dict['gold'], pos, [self.all_sprites, self.coin_sprites])
					case 5: Coin('silver', asset_dict['silver'], pos, [self.all_sprites, self.coin_sprites])
					case 6: Coin('diamond', asset_dict['diamond'], pos, [self.all_sprites, self.coin_sprites])

					# enemies
					case 7: Spikes(asset_dict['spikes'], pos, [self.all_sprites, self.damage_sprites])
					case 8: Tooth(asset_dict['tooth'], pos, [self.all_sprites, self.damage_sprites])
					case 9: Shell('left', asset_dict['shell'], pos, self.all_sprites)
					case 10: Shell('right', asset_dict['shell'], pos, self.all_sprites)

					# palm trees
					case 11: Animated(asset_dict['palms']['small_fg'], pos, self.all_sprites)
					case 12: Animated(asset_dict['palms']['large_fg'], pos, self.all_sprites)
					case 13: Animated(asset_dict['palms']['left_fg'], pos, self.all_sprites)
					case 14: Animated(asset_dict['palms']['right_fg'], pos, self.all_sprites)
					case 15: Animated(asset_dict['palms']['small_bg'], pos, self.all_sprites)
					case 16: Animated(asset_dict['palms']['large_bg'], pos, self.all_sprites)
					case 17: Animated(asset_dict['palms']['left_bg'], pos, self.all_sprites)
					case 18: Animated(asset_dict['palms']['right_bg'], pos, self.all_sprites)

	def get_coins(self):
		collided_coins = pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
		for sprite in collided_coins:
			Particle(self.particle_surfs, sprite.rect.center, self.all_sprites)

	def event_loop(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				self.switch()

	def run(self, dt):
		# update
		self.event_loop()
		self.all_sprites.update(dt)
		self.get_coins()

		# drawing
		self.display_surface.fill(SKY_COLOR)
		self.all_sprites.draw(self.display_surface)
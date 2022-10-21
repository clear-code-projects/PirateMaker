import pygame
from pygame.math import Vector2 as vector

from settings import *

class Generic(pygame.sprite.Sprite):
	def __init__(self, pos, surf, group):
		super().__init__(group)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)


# simple animated objects
class Animated(Generic):
	def __init__(self, assets, pos, group):
		self.animation_frames = assets
		self.frame_index = 0
		super().__init__(pos, self.animation_frames[self.frame_index], group)

	def animate(self, dt):
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index = 0 if self.frame_index >= len(self.animation_frames) else self.frame_index
		self.image = self.animation_frames[int(self.frame_index)]

	def update(self, dt):
		self.animate(dt)

class Particle(Animated):
	def __init__(self, assets, pos, group):
		super().__init__(assets, pos, group)
		self.rect = self.image.get_rect(center = pos)

	def animate(self, dt):
		self.frame_index += ANIMATION_SPEED * dt
		if self.frame_index < len(self.animation_frames):
			self.image = self.animation_frames[int(self.frame_index)]
		else:
			self.kill()

class Coin(Animated):
	def __init__(self, coin_type, assets, pos, group):
		super().__init__(assets, pos, group)
		self.rect = self.image.get_rect(center = pos)
		self.coin_type = coin_type


# enemies
class Spikes(Generic):
	def __init__(self, surf, pos, group):
		super().__init__(pos, surf, group)

class Tooth(Generic):
	def __init__(self, assets, pos, group):

		self.animation_frames = assets
		self.frame_index = 0
		self.orientation = 'right'
		surf = self.animation_frames[f'run_{self.orientation}'][self.frame_index]
		super().__init__(pos, surf, group)
		self.rect.bottom = self.rect.top + TILE_SIZE

class Shell(Generic):
	def __init__(self, orientation, assets, pos, group):
		self.orientation = orientation
		self.animation_frames = assets.copy()
		if orientation == 'right':
			for key, value in self.animation_frames.items():
				self.animation_frames[key] = [pygame.transform.flip(surf,True,False) for surf in value]

		self.frame_index = 0
		self.status = 'idle'
		super().__init__(pos, self.animation_frames[self.status][self.frame_index], group)
		self.rect.bottom = self.rect.top + TILE_SIZE

class Player(Generic):
	def __init__(self, pos, group):
		super().__init__(pos, pygame.Surface((32,64)), group)
		self.image.fill('red')

		# movement
		self.direction = vector()
		self.pos = vector(self.rect.topleft)
		self.speed = 300

	def input(self):
		keys = pygame.key.get_pressed()
		if keys[pygame.K_RIGHT]:
			self.direction.x = 1
		elif keys[pygame.K_LEFT]:
			self.direction.x = -1
		else:
			self.direction.x = 0

	def move(self, dt):
		self.pos += self.direction * self.speed * dt
		self.rect.topleft = (round(self.pos.x),round(self.pos.y))


	def update(self, dt):
		self.input()
		self.move(dt)

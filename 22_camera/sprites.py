import pygame
from pygame.math import Vector2 as vector

from settings import *

class Generic(pygame.sprite.Sprite):
	def __init__(self, pos, surf, group, z = LEVEL_LAYERS['main']):
		super().__init__(group)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = z

class Block(Generic):
	def __init__(self, pos, size, group):
		surf = pygame.Surface(size)
		super().__init__(pos, surf, group)


# simple animated objects
class Animated(Generic):
	def __init__(self, assets, pos, group, z = LEVEL_LAYERS['main']):
		self.animation_frames = assets
		self.frame_index = 0
		super().__init__(pos, self.animation_frames[self.frame_index], group, z)

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
	def __init__(self, pos, assets, group, collision_sprites):
		
		# animation
		self.animation_frames = assets
		self.frame_index = 0
		self.status = 'idle'
		self.orientation = 'right'
		surf = self.animation_frames[f'{self.status}_{self.orientation}'][self.frame_index]
		super().__init__(pos, surf, group)

		# movement
		self.direction = vector()
		self.pos = vector(self.rect.center)
		self.speed = 300
		self.gravity = 4
		self.on_floor = False

		# collision
		self.collision_sprites = collision_sprites
		self.hitbox = self.rect.inflate(-50,0)

	def get_status(self):
		if self.direction.y < 0:
			self.status = 'jump'
		elif self.direction.y > 1:
			self.status = 'fall'
		else:
			self.status = 'run' if self.direction.x != 0 else 'idle'

	def animate(self, dt):
		current_animation = self.animation_frames[f'{self.status}_{self.orientation}']
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index = 0 if self.frame_index >= len(current_animation) else self.frame_index
		self.image = current_animation[int(self.frame_index)]

	def input(self):
		keys = pygame.key.get_pressed()
		if keys[pygame.K_RIGHT]:
			self.direction.x = 1
			self.orientation = 'right'
		elif keys[pygame.K_LEFT]:
			self.direction.x = -1
			self.orientation = 'left'
		else:
			self.direction.x = 0

		if keys[pygame.K_SPACE] and self.on_floor:
			self.direction.y = -2

	def move(self, dt):
		
		# horizontal movement
		self.pos.x += self.direction.x * self.speed * dt
		self.hitbox.centerx = round(self.pos.x)
		self.rect.centerx = self.hitbox.centerx
		self.collision('horizontal')

		# vertical movement
		self.pos.y += self.direction.y * self.speed * dt
		self.hitbox.centery = round(self.pos.y)
		self.rect.centery = self.hitbox.centery
		self.collision('vertical')

	def apply_gravity(self, dt):
		self.direction.y += self.gravity * dt
		self.rect.y += self.direction.y

	def check_on_floor(self):
		floor_rect = pygame.Rect(self.hitbox.bottomleft,(self.hitbox.width,2))
		floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.colliderect(floor_rect)]
		self.on_floor = True if floor_sprites else False

	def collision(self, direction):
		for sprite in self.collision_sprites:
			if sprite.rect.colliderect(self.hitbox):
				if direction == 'horizontal':
					self.hitbox.right = sprite.rect.left if self.direction.x > 0 else self.hitbox.right
					self.hitbox.left = sprite.rect.right if self.direction.x < 0 else self.hitbox.left
					self.rect.centerx, self.pos.x = self.hitbox.centerx, self.hitbox.centerx
				else: # vertical
					self.hitbox.top = sprite.rect.bottom if self.direction.y < 0 else self.hitbox.top
					self.hitbox.bottom = sprite.rect.top if self.direction.y > 0 else self.hitbox.bottom
					self.rect.centery, self.pos.y = self.hitbox.centery, self.hitbox.centery
					self.direction.y = 0

	def update(self, dt):
		self.input()
		self.apply_gravity(dt)
		self.move(dt)
		self.check_on_floor()

		self.get_status()
		self.animate(dt)

import pygame
from pygame.math import Vector2 as vector

class Generic(pygame.sprite.Sprite):
	def __init__(self, pos, surf, group):
		super().__init__(group)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)

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

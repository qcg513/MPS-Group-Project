import pygame

pygame.init()

iterations = 8	
screen = pygame.display.set_mode((3 ** iterations, 3 ** iterations))

save_on_exit = False
def save():
	pygame.image.save(screen, 'carpet.png')

## Creating the carpet ##

# Unlike the mandelbrot set viewer, only two colours are required for the image of the carpet
black = (0, 0, 0)
white = (255, 255, 255)

# Iteration 1
width = 3
carpet = pygame.Surface((width, width))

pixel_array = pygame.PixelArray(carpet)
pixel_array[0] = [black, black, black]
pixel_array[1] = [black, white, black]
pixel_array[2] = [black, black, black]
pixel_array.close()

# Other iterations

for i in range(iterations - 1):
	new_carpet = pygame.Surface((3 * width, 3 * width))
	new_carpet.fill(white)
	for x in range(3):
		for y in range(3):
			if (x == 1) and (y == 1):
				continue

			new_carpet.blit(carpet, (x * width, y * width))

	width *= 3
	carpet = new_carpet.copy()

running = True
while running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

			if save_on_exit: save()

			pygame.quit()

	screen.blit(carpet, (0, 0))
	pygame.display.flip()
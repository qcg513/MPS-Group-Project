import pygame
from math import fabs
from time import perf_counter

pygame.init()

width = 201			# The number of pixels wide to calculate the mandelbrot set to
scaling_factor = 6  # The scaling factor from the number of pixels calculated to the actual display size of the window
window = pygame.display.set_mode((scaling_factor * width, scaling_factor * width))

surface = pygame.Surface((width, width))
px_array = pygame.PixelArray(surface)

# This is the world-space position of the top_left of the screen
top_left = pygame.math.Vector2()
top_left.xy = -1.5,1
zoom = (width - 1) // 2
zooming_factor = 1.41	# The factor that the screen should zoom into when pressing either of the "-" or "=" buttons to zoom out and in respectively

### Mandelbrot Settings ###
save_on_exit = False	# Saves a the mandelbrot set image when the window is closed (if it is fully drawn)
max_iterations = 50		# The number of iterations to check if a point stays within 
cut_off = 2 			# The limit before a point is considered tend off to infinity
batch_size = 5 		# The number of lines to calculate before checking the time

def display_to_world(x, y):
	# Translates from the screen position space to the complex plane that the program uses to calculate the colours of the pixels.
	# The x and y coordinates passed as parameters are measured in pixels to the left border and top border of the screen respectively.
	return ((x / zoom) + top_left.x,
			-(y / zoom) + top_left.y)

def iterate(z, c):
	# Performs one iteration of the sequence defining the mandelbrot set
	new_z = pygame.math.Vector2()
	new_z.x = z.x * z.x - z.y * z.y + c.x
	new_z.y = 2 * z.x * z.y + c.y
	return new_z

def colourise(iterations_to_leave):
	# This function calculates the percentage of the maximum number of iterations that it took the point to leave the cutoff region.
	# It then uses that to index into the rgb colour space in the same way that the bottom rainbow-colour slider works on this website: https://rgbcolorpicker.com/ 
	# Note, this is not specific to this source, for extra reading, see https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_RGB

	depth = iterations_to_leave / max_iterations

	if depth <= 1/6:
		return (251, 43 + int(208 * (6 * depth)), 43)
	elif depth <= 2/6:
		return (251 - int(208 * 6 * (depth - 1/6)), 251, 43)
	elif depth <= 3/6:
		return (43, 251, 43 + int(208 * 6 * (depth - 2/6)))
	elif depth <= 4/6:
		return (43, 251 - int(208 * 6 * (depth - 3/6)), 251)
	elif depth <= 5/6:
		return (43 + int(208 * 6 * (depth - 4/6)), 43, 251)
	else:
		return (251, 43, 251 - int(208 * 6 * (depth - 5/6)))

def compute_line(y):
	# Computes all the pixels for a specific y-level
	global px_array

	for x in range(width):
		c = pygame.math.Vector2(display_to_world(x,y))
		z = c.copy()

		count = 0
		out_of_bounds = False
		while (not out_of_bounds) and (count < max_iterations):
			z = iterate(z, c)
			out_of_bounds = (fabs(z.x) > cut_off) or (fabs(z.y) > cut_off)
			count += 1

		if out_of_bounds:	px_array[x,y] = colourise(count)
		else: 				px_array[x,y] = (0, 0, 0)

def save():
	pygame.image.save(surface, 'mandelbrot.png')

clock = pygame.time.Clock()
fps = 10
line_num = 0

running = True
while running:
	# The start time of the frame is used to determine when we should stop calculating new pixels and output the already-calculated ones to the display
	start = perf_counter()

	
	world_screen_width = (width - 1) / zoom 	# The width of the complex plane displayed
	
	# This handles the various user inputs that the program should respond to
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
			if (save_on_exit) and (end_y_val == width): save()

		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_q:
				print("Quitted")
				running = False
				if save_on_exit: save()

			elif event.key == pygame.K_MINUS:
				# Zooms out of the centre by increasing the zoom and moving the top-left position by an appropriate amount
				width_coefficient = 1 / (zooming_factor * 2)
				top_left.x -= world_screen_width * width_coefficient
				top_left.y += world_screen_width * width_coefficient
				line_num = 0
				zoom /= zooming_factor

			elif event.key == pygame.K_EQUALS:
				# Zooms into the centre by increasing the zoom and moving the top-left position by an appropriate amount
				zoom *= zooming_factor
				world_screen_width = (width - 1) / zoom

				width_coefficient = 1 / (zooming_factor * 2)
				top_left.x += world_screen_width * width_coefficient
				top_left.y -= world_screen_width * width_coefficient
				line_num = 0

			elif event.key == pygame.K_LEFT:
				top_left.x -= world_screen_width * 0.2
				line_num = 0

			elif event.key == pygame.K_RIGHT:
				top_left.x += world_screen_width * 0.2
				line_num = 0

			elif event.key == pygame.K_UP:
				top_left.y += world_screen_width * 0.2
				line_num = 0

			elif event.key == pygame.K_DOWN:
				top_left.y -= world_screen_width * 0.2
				line_num = 0

		# elif event.type == pygame.MOUSEWHEEL:
		# 	mouse_pos = pygame.mouse.get_pos()
		# 	print(display_to_world(mouse_pos[0] / scaling_factor, mouse_pos[1] / scaling_factor))

	if line_num < width:
		# While there is still time left in the frame, the program calculates the pixels for successive y-values
		while (perf_counter() - start < (1/fps)):
			end_y_val = width
			if (end_y_val - line_num > 10): 
				end_y_val = line_num + 10
			
			for y_val in range(line_num, end_y_val):
				compute_line(y_val)

			line_num = end_y_val
			#print(f"Calculated up to y={end_y_val}")

			if end_y_val == width:
				#print("Finished rendereing")
				break

	
	window.blit(pygame.transform.scale(surface, window.get_rect().size), (0, 0))
	pygame.display.update()
	clock.tick(fps)

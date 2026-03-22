import pygame
import math
import argparse		# A library for parsing command-line arguments
from time import perf_counter

##### Initial Setup of Variables #####

width = 601			# The number of pixels wide to calculate the mandelbrot set to
scaling_factor = 1  # The scaling factor from the number of pixels calculated to the actual display size of the window

# This is the world-space position of the top_left of the screen
top_left = pygame.math.Vector2()
zoom = 0
zooming_factor = 1.41	# The factor that the screen should zoom into when pressing either of the "-" or "=" buttons to zoom out and in respectively

# Determining which fractal to generate
fractals_available = ["mandelbrot", "julia", "burning_ship", "lyapunov"]
fractal_to_draw = 3 	# The index of the fractal that you wish to generate

### Fractal Generator Settings ###
save_on_exit = False	# Saves a the mandelbrot set image when the window is closed (if it is fully drawn)
max_iterations = 100	# The number of iterations to check if a point stays within 
cut_off = 2 			# The limit before a point is considered tend off to infinity
batch_size = 5 		# The number of lines to calculate before checking the time
file_name = "fractal.png"

##### Argument Parsing #####

if (__name__ == "__main__"):
	### Initialize the argument parser and add the arguments
	parser = argparse.ArgumentParser(description="A fractal generating script")
	
	parser.add_argument("--s",
		type=str,
		default="False",
		choices=["True", "False"], 
		help="Whether or not to save the rendered image to a file"
	)
	parser.add_argument("--file",
		type=str,
		default=file_name,
		help="The filename to save the image with"
	)
	parser.add_argument("--fractal",
		type=str,
		default="mandelbrot",
		choices=fractals_available,
		help="The fractal to draw"
	)
	parser.add_argument("--pixel_width",
		type=int,
		default=width,
		help="The width in pixels of the calculated image"
	)

	args = parser.parse_args()

	save_on_exit = True if (args.s == "True") else False
	file_name = args.file
	fractal_to_draw = fractals_available.index(args.fractal)
	width=args.pixel_width
	zoom = (width - 1) // 2 	# Calculate the zoom once the width has been set

	if (fractal_to_draw == 3):
		top_left.xy = 2,4 		# A good starting point for the lyapunov fractal
	else:
		top_left.xy = -1.5,1 	# A good starting point for the iterative fractals

##### Initializing the Pygame Environment

pygame.init()				# Initialize the pygame module
clock = pygame.time.Clock()	# Initialize the clock to provide consistent frame-times
fps = 10

window = pygame.display.set_mode((scaling_factor * width, scaling_factor * width))
surface = pygame.Surface((width, width))
px_array = pygame.PixelArray(surface)

##### Function Definitions #####

def display_to_world(x, y):
	# Translates from the screen position space to the complex plane that the program uses to calculate the colours of the pixels.
	# The x and y coordinates passed as parameters are measured in pixels to the left border and top border of the screen respectively.
	return ((x / zoom) + top_left.x,
			-(y / zoom) + top_left.y)

def mandel_iterate(z, c):
	# Performs one iteration of the sequence defining the mandelbrot set
	new_z = pygame.math.Vector2()
	new_z.x = z.x * z.x - z.y * z.y + c.x
	new_z.y = 2 * z.x * z.y + c.y
	return new_z

julia_c = pygame.math.Vector2((0, 0))	# The constant for the julia set
def julia_iterate(z):
	return mandel_iterate(z, julia_c)

def burning_ship_iterate(z, c):
	# Performs an iteration defining the burning ship fractal, this is very similar to the mandelbrot set, except absolute value of the real and imaginary components of z are used instead.
	new_z = pygame.math.Vector2()
	new_z.x = z.x * z.x - z.y * z.y + c.x
	new_z.y = 2 * math.fabs(z.x * z.y) + c.y
	return new_z

# The lyapunov fractals are a strange family of fractals defined by a sequences of A's and B's
# Further reading: https://en.wikipedia.org/wiki/Lyapunov_fractal
sequence = 'AABAB'
def lyapunov_sequence_index(n):
	# Indexes into the sequences of A's and B's
	# Returns True for an A and False for a B
	return sequence[(n+1) % len(sequence)] == 'A' 

def lyapunov_map(lam):
	# This function maps the values of lambda that exist in (-\infty, \infty) to (0, 1) so that they can be coloured correctly
	return 0.5 * (1 + math.sin(math.atan(lam / 100)))

def lyapunov_pixel_calc(z):
	total = 0
	x = 0.5

	for n in range(max_iterations):
		r_n = z.x if lyapunov_sequence_index(n) else z.y
		x = r_n * x * (1 - x)
		if math.fabs(x) == 1/2:
			#print(f"Failed on iteration {n} of point {z.x},{z.y}")
			break

		total += math.log(math.fabs(r_n * (1 - 2 * x)))

	#print(f"At point ({z.x},{z.y}) value: {total}")

	return True, lyapunov_map(total)

def colourise(depth):
	# This function uses the depth to index into the rgb colour space in the same way that the bottom rainbow-colour slider works on this website: https://rgbcolorpicker.com/ 
	# Note, this is not specific to this source, for extra reading, see https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_RGB

	if depth <= 0:
		return (255, 255, 255)
	elif depth <= 1/6:
		return (251, 43 + int(208 * (6 * depth)), 43)
	elif depth <= 2/6:
		return (251 - int(208 * 6 * (depth - 1/6)), 251, 43)
	elif depth <= 3/6:
		return (43, 251, 43 + int(208 * 6 * (depth - 2/6)))
	elif depth <= 4/6:
		return (43, 251 - int(208 * 6 * (depth - 3/6)), 251)
	elif depth <= 5/6:
		return (43 + int(208 * 6 * (depth - 4/6)), 43, 251)
	elif depth <= 1:
		return (251, 43, 251 - int(208 * 6 * (depth - 5/6)))
	else:
		return (0, 0, 0)

def compute_pixel_iterative(c) -> int:
	z = c.copy()	# Copy the value of c into z to skip the first iteration
	count = 0
	out_of_bounds = False
	while (not out_of_bounds) and (count < max_iterations):
		match fractal_to_draw:
			case 0:
				# Drawing the mandelbrot set
				z = mandel_iterate(z, c)
			case 1:
				# Drawing the Julia set
				z = julia_iterate(z)
			case 2:
				# Drawing the burning ship
				z = burning_ship_iterate(z, c)

		out_of_bounds = (math.fabs(z.x) > cut_off) or (math.fabs(z.y) > cut_off)
		count += 1

	return (out_of_bounds, count / max_iterations)

def compute_line(y):
	# Computes all the pixels for a specific y-level
	global px_array

	for x in range(width):
		c = pygame.math.Vector2(display_to_world(x,y))
		
		if fractal_to_draw == 3:
			out_of_bounds, depth = lyapunov_pixel_calc(c)
			
		else: out_of_bounds, depth = compute_pixel_iterative(c)

		if out_of_bounds:	px_array[x,y] = colourise(depth)
		else: 				px_array[x,y] = (0, 0, 0)

def save():
	pygame.image.save(surface, file_name)


##### The Main Loop of the Renderer #####

running = True
line_num = 0
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
			if (end_y_val - line_num > batch_size): 
				end_y_val = line_num + batch_size
			
			for y_val in range(line_num, end_y_val):
				compute_line(y_val)

			line_num = end_y_val
			#print(f"Calculated up to y={end_y_val}")

			if end_y_val == width:
				print("Finished rendereing")
				break

	# Scales the surface with the calculated pixels on it up by the scaling factor and then places it onto the window's surface
	window.blit(pygame.transform.scale(surface, window.get_rect().size), (0, 0))
	pygame.display.update()	# Updates the display to show the new surface
	clock.tick(fps)			# Limits the number of frames presented per second to the value of "fps"

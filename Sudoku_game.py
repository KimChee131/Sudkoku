import pygame
import sys
import random
import time
import json
import os

# Initialize pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
LIGHT_RED = (255, 200, 200)
LIGHT_GREEN = (200, 255, 200)
YELLOW = (255, 255, 0)
PURPLE = (200, 0, 200)
ORANGE = (255, 165, 0)

# Screen dimensions
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 750
GRID_SIZE = 9
CELL_SIZE = 600 // GRID_SIZE
GRID_OFFSET = 300

# Fonts
FONT = pygame.font.SysFont('Arial', 40)
SMALL_FONT = pygame.font.SysFont('Arial', 20)
NOTE_FONT = pygame.font.SysFont('Arial', 15)
TITLE_FONT = pygame.font.SysFont('Arial', 50)

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Sudoku')

# High scores file
HIGH_SCORES_FILE = "sudoku_scores.json"

class Sudoku:
	def __init__(self, difficulty=0.5):
		self.board = [[0 for _ in range(9)] for _ in range(9)] # Khởi tạo bảng chơi toàn số 0
		self.solution = [[0 for _ in range(9)] for _ in range(9)] # Lưu lời giả hoàn chỉnh
		self.user_input = [[0 for _ in range(9)] for _ in range(9)] # Ghi lại số người chơi đã nhập
		self.notes = [[[False for _ in range(9)] for _ in range(9)] for _ in range(9)] # Ghi lại ghi chú
		self.locked = [[False for _ in range(9)] for _ in range(9)] # Ô là số gốc thì không thể sửa
		self.incorrect_cells = set() # Tập hợp chứa tọa độ các ô nhập sai
		self.selected = None # Tọa độ của ô đang được chọn 
		self.start_time = time.time() # Thời gian bắt đầu chơi (để tính giờ)
		self.elapsed_time = 0 # Thời gian đã chơi (tính đến hiện tại)
		self.mistakes = 0 # Số lần nhập sai
		self.game_over = False # Cờ báo hiệu trò chơi kết thúc hay chưa
		self.difficulty = difficulty # Mức độ khó của trò chơi
		self.history = [] # Lưu lịch sử thao tác (để hoàn tác)
		self.generate_board(difficulty) # Sinh bảng theo độ khó
		
	def generate_board(self, difficulty):
		# Reset board
		self.board = [[0 for _ in range(9)] for _ in range(9)]
		
		# Fill diagonal boxes randomly
		self.fill_diagonal()
		
		# Solve the complete board
		self.solve_board(self.board)
		
		# Save the solution
		for i in range(9):
			for j in range(9):
				self.solution[i][j] = self.board[i][j]
		
		# Set difficulty levels
		difficulty_levels = {
			"easy": 0.5,    # Remove ~50% of numbers
			"medium": 0.6,   # Remove ~60% of numbers
			"hard": 0.7      # Remove ~70% of numbers
		}
		
		if isinstance(difficulty, str):
			difficulty = difficulty_levels.get(difficulty, 0.6)
		
		# Prepare cells to remove
		cells = [(i, j) for i in range(9) for j in range(9)]
		random.shuffle(cells)
		to_remove = int(81 * difficulty)
		
		# Remove numbers to create puzzle
		for i in range(to_remove):
			row, col = cells[i]
			self.board[row][col] = 0
	
	def fill_diagonal(self):
		"""Fill the diagonal 3x3 boxes with random numbers"""
		for box in range(0, 9, 3):
			nums = list(range(1, 10))
			random.shuffle(nums)
			for i in range(3):
				for j in range(3):
					self.board[box + i][box + j] = nums.pop()
	
	def is_valid(self, board, row, col, num):
		# Check row
		if num in board[row]:
			return False
		
		# Check column
		for i in range(9):
			if board[i][col] == num:
				return False
		
		# Check 3x3 box
		start_row, start_col = 3 * (row // 3), 3 * (col // 3)
		for i in range(3):
			for j in range(3):
				if board[start_row + i][start_col + j] == num:
					return False
		
		return True
	
	def solve_board(self, board):
		for row in range(9):
			for col in range(9):
				if board[row][col] == 0:
					for num in random.sample(range(1, 10), 9):  # Try numbers in random order
						if self.is_valid(board, row, col, num):
							board[row][col] = num
							if self.solve_board(board):
								return True
							board[row][col] = 0
					return False
		return True
	
	def place_number(self, row, col, num):
		if self.locked[row][col]:
			return False  # Không cho sửa ô đã bị khóa
		
		self.save_state()
		
		# Clear any notes for this cell
		for i in range(9):
			self.notes[row][col][i] = False
		
		if num == 0:
			self.user_input[row][col] = 0
			self.incorrect_cells.discard((row, col))
			return True
		
		if self.solution[row][col] == num:
			self.user_input[row][col] = num
			self.incorrect_cells.discard((row, col))
			self.locked[row][col] = True
			return True
		else:
			self.user_input[row][col] = num
			self.incorrect_cells.add((row, col))
			self.mistakes += 1
			return False
	
	def toggle_note(self, row, col, num):
		if self.locked[row][col]:
			return 

		if self.board[row][col] == 0 and self.user_input[row][col] == 0:
			self.save_state()
			self.notes[row][col][num-1] = not self.notes[row][col][num-1]
	
	def clear_notes(self, row, col):
		if any(self.notes[row][col]):
			self.save_state()
			for i in range(9):
				self.notes[row][col][i] = False
	
	def save_state(self):
		state = {
			'user_input': [row[:] for row in self.user_input],
			'notes': [[col[:] for col in row] for row in self.notes],
			'incorrect_cells': set(self.incorrect_cells),
			'mistakes': self.mistakes
		}
		self.history.append(state)
	
	def undo(self):
		if self.history:
			state = self.history.pop()
			self.user_input = [row[:] for row in state['user_input']]
			self.notes = [[col[:] for col in row] for row in state['notes']]
			self.incorrect_cells = set(state['incorrect_cells'])
	
	def is_complete(self):
		for row in range(9):
			for col in range(9):
				if self.board[row][col] == 0 and (row, col) not in self.incorrect_cells and self.user_input[row][col] == 0:
					return False
		self.game_over = True
		self.save_score()
		return True
	
	def save_score(self):
		scores = self.load_scores()
		
		score_entry = {
			'time': int(self.elapsed_time),
			'mistakes': self.mistakes,
			'difficulty': self.difficulty,
			'date': time.strftime("%Y-%m-%d %H:%M:%S")
		}
		
		if isinstance(self.difficulty, str):
			diff_key = self.difficulty
		else:
			if self.difficulty < 0.55:
				diff_key = "easy"
			elif self.difficulty < 0.65:
				diff_key = "medium"
			else:
				diff_key = "hard"
		
		if diff_key not in scores:
			scores[diff_key] = []
		
		scores[diff_key].append(score_entry)
		scores[diff_key].sort(key=lambda x: (x['time'], x['mistakes']))
		scores[diff_key] = scores[diff_key][:10]
		
		with open(HIGH_SCORES_FILE, 'w') as f:
			json.dump(scores, f)
	
	def load_scores(self):
		try:
			if os.path.exists(HIGH_SCORES_FILE):
				with open(HIGH_SCORES_FILE, 'r') as f:
					return json.load(f)
		except:
			pass
		return {}
	
	def update_time(self):
		if not self.game_over:
			self.elapsed_time = time.time() - self.start_time

def draw_grid():
	# Draw the left panel background
	pygame.draw.rect(screen, LIGHT_BLUE, (0, 0, 300, SCREEN_HEIGHT))
	
	# Draw the grid background (right side)
	pygame.draw.rect(screen, WHITE, (300, 0, 600, 600))
	
	# Draw grid lines (right side)
	for i in range(0, 10, 3):
		pygame.draw.line(screen, BLACK, (GRID_OFFSET, i * CELL_SIZE), (GRID_OFFSET + 600, i * CELL_SIZE), 4)
		pygame.draw.line(screen, BLACK, (i * CELL_SIZE + GRID_OFFSET, 0), (i * CELL_SIZE + GRID_OFFSET, 600), 4)
	
	for i in range(1, 9):
		if i % 3 != 0:
			pygame.draw.line(screen, GRAY, (GRID_OFFSET, i * CELL_SIZE), (GRID_OFFSET + 600, i * CELL_SIZE), 1)
			pygame.draw.line(screen, GRAY, (i * CELL_SIZE + GRID_OFFSET, 0), (i * CELL_SIZE + GRID_OFFSET, 600), 1)

def draw_numbers(board, user_input, notes, incorrect_cells, selected=None, note_mode=False):
	for row in range(9):
		for col in range(9):
			if board[row][col] != 0:
				x = col * CELL_SIZE + CELL_SIZE // 2 + GRID_OFFSET
				y = row * CELL_SIZE + CELL_SIZE // 2
				num_text = FONT.render(str(board[row][col]), True, BLACK)
				num_rect = num_text.get_rect(center=(x, y))
				screen.blit(num_text, num_rect)
			elif user_input[row][col] != 0:
				x = col * CELL_SIZE + CELL_SIZE // 2 + GRID_OFFSET
				y = row * CELL_SIZE + CELL_SIZE // 2
				
				if selected and selected == (row, col):
					pygame.draw.rect(screen, LIGHT_BLUE, (col * CELL_SIZE + GRID_OFFSET, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
				
				if (row, col) in incorrect_cells:
					pygame.draw.rect(screen, LIGHT_RED, (col * CELL_SIZE + GRID_OFFSET, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
				
				num_text = FONT.render(str(user_input[row][col]), True, RED if (row, col) in incorrect_cells else BLACK)
				num_rect = num_text.get_rect(center=(x, y))
				screen.blit(num_text, num_rect)
			else:
				if selected and selected == (row, col) and note_mode:
					pygame.draw.rect(screen, ORANGE, (col * CELL_SIZE + GRID_OFFSET, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
				
				for num in range(9):
					if notes[row][col][num]:
						note_x = col * CELL_SIZE + (num % 3) * (CELL_SIZE // 3) + (CELL_SIZE // 6) + GRID_OFFSET
						note_y = row * CELL_SIZE + (num // 3) * (CELL_SIZE // 3) + (CELL_SIZE // 6)
						note_text = NOTE_FONT.render(str(num+1), True, PURPLE)
						note_rect = note_text.get_rect(center=(note_x, note_y))
						screen.blit(note_text, note_rect)
	
	if selected:
		row, col = selected
		border_color = ORANGE if note_mode else GREEN
		pygame.draw.rect(screen, border_color, (col * CELL_SIZE + GRID_OFFSET, row * CELL_SIZE, CELL_SIZE, CELL_SIZE), 3)

def draw_controls(note_mode=False):
	button_size = 50
	margin = 20
	start_x = margin
	start_y = margin
	
	# Draw number buttons 1-9 in 3x3 grid
	for i in range(1, 10):
		row = (i-1) // 3
		col = (i-1) % 3
		x = start_x + col * (button_size + margin)
		y = start_y + row * (button_size + margin)
		
		pygame.draw.rect(screen, WHITE, (x, y, button_size, button_size))
		num_text = FONT.render(str(i), True, BLACK)
		num_rect = num_text.get_rect(center=(x + button_size//2, y + button_size//2))
		screen.blit(num_text, num_rect)
	
	# Clear button (X)
	y = start_y + 3 * (button_size + margin) + margin
	pygame.draw.rect(screen, WHITE, (start_x, y, button_size*3 + margin*2, button_size))
	num_text = FONT.render("Clear", True, BLACK)
	num_rect = num_text.get_rect(center=(start_x + (button_size*3 + margin*2)//2, y + button_size//2))
	screen.blit(num_text, num_rect)
	
	# Note mode button (N)
	y += button_size + margin
	button_color = YELLOW if note_mode else WHITE
	pygame.draw.rect(screen, button_color, (start_x, y, button_size*3 + margin*2, button_size))
	note_text = FONT.render("Notes", True, BLACK)
	note_rect = note_text.get_rect(center=(start_x + (button_size*3 + margin*2)//2, y + button_size//2))
	screen.blit(note_text, note_rect)
	
	# Undo button (U)
	y += button_size + margin
	pygame.draw.rect(screen, WHITE, (start_x, y, button_size*3 + margin*2, button_size))
	undo_text = FONT.render("Undo", True, BLACK)
	undo_rect = undo_text.get_rect(center=(start_x + (button_size*3 + margin*2)//2, y + button_size//2))
	screen.blit(undo_text, undo_rect)
	
	# Menu button
	y += button_size + margin
	pygame.draw.rect(screen, WHITE, (start_x, y, button_size*3 + margin*2, button_size))
	menu_text = FONT.render("Menu", True, BLACK)
	menu_rect = menu_text.get_rect(center=(start_x + (button_size*3 + margin*2)//2, y + button_size//2))
	screen.blit(menu_text, menu_rect)
	
	# Display time and mistakes at bottom of left panel
	time_text = SMALL_FONT.render(f"Time: {int(game.elapsed_time)}s", True, BLACK)
	mistakes_text = SMALL_FONT.render(f"Mistakes: {game.mistakes}", True, BLACK)
	
	screen.blit(time_text, (start_x, SCREEN_HEIGHT - 60))
	screen.blit(mistakes_text, (start_x, SCREEN_HEIGHT - 30))
	
	# Return button rects for click detection
	clear_rect = pygame.Rect(start_x, start_y + 3*(button_size + margin) + margin, button_size*3 + margin*2, button_size)
	note_rect = pygame.Rect(start_x, y - 2*(button_size + margin), button_size*3 + margin*2, button_size)
	undo_rect = pygame.Rect(start_x, y - (button_size + margin), button_size*3 + margin*2, button_size)
	menu_rect = pygame.Rect(start_x, y, button_size*3 + margin*2, button_size)
	
	# Return number buttons rects (3x3 grid)
	number_rects = []
	for i in range(1, 10):
		row = (i-1) // 3
		col = (i-1) % 3
		x = start_x + col * (button_size + margin)
		y = start_y + row * (button_size + margin)
		number_rects.append(pygame.Rect(x, y, button_size, button_size))
	
	return clear_rect, note_rect, undo_rect, menu_rect, number_rects

def draw_game_over():
	overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
	overlay.fill((0, 0, 0, 128))
	screen.blit(overlay, (0, 0))
	
	game_over_text = FONT.render("Puzzle Complete!", True, WHITE)
	time_text = FONT.render(f"Time: {int(game.elapsed_time)}s", True, WHITE)
	mistakes_text = FONT.render(f"Mistakes: {game.mistakes}", True, WHITE)
	restart_text = SMALL_FONT.render("Press R to restart or ESC to exit", True, WHITE)
	
	screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
	screen.blit(time_text, (SCREEN_WIDTH//2 - time_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
	screen.blit(mistakes_text, (SCREEN_WIDTH//2 - mistakes_text.get_width()//2, SCREEN_HEIGHT//2 + 40))
	screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 100))

def draw_menu():
	screen.fill(WHITE)
	
	title_text = TITLE_FONT.render("Sudoku", True, BLACK)
	screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
	
	easy_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 200, 200, 50)
	medium_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 280, 200, 50)
	hard_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 360, 200, 50)
	scores_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 440, 200, 50)
	
	pygame.draw.rect(screen, LIGHT_GREEN, easy_rect)
	pygame.draw.rect(screen, YELLOW, medium_rect)
	pygame.draw.rect(screen, LIGHT_RED, hard_rect)
	pygame.draw.rect(screen, LIGHT_BLUE, scores_rect)
	
	easy_text = FONT.render("Easy", True, BLACK)
	medium_text = FONT.render("Medium", True, BLACK)
	hard_text = FONT.render("Hard", True, BLACK)
	scores_text = FONT.render("High Scores", True, BLACK)
	
	screen.blit(easy_text, (easy_rect.centerx - easy_text.get_width()//2, easy_rect.centery - easy_text.get_height()//2))
	screen.blit(medium_text, (medium_rect.centerx - medium_text.get_width()//2, medium_rect.centery - medium_text.get_height()//2))
	screen.blit(hard_text, (hard_rect.centerx - hard_text.get_width()//2, hard_rect.centery - hard_text.get_height()//2))
	screen.blit(scores_text, (scores_rect.centerx - scores_text.get_width()//2, scores_rect.centery - scores_text.get_height()//2))
	
	return easy_rect, medium_rect, hard_rect, scores_rect

def draw_scores():
	screen.fill(WHITE)
	
	title_text = TITLE_FONT.render("High Scores", True, BLACK)
	screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 30))
	
	back_rect = pygame.Rect(20, 20, 100, 40)
	pygame.draw.rect(screen, LIGHT_BLUE, back_rect)
	back_text = SMALL_FONT.render("Back", True, BLACK)
	screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, back_rect.centery - back_text.get_height()//2))
	
	scores = game.load_scores()
	y_offset = 100
	
	for difficulty in ["easy", "medium", "hard"]:
		if difficulty in scores and scores[difficulty]:
			diff_text = FONT.render(f"{difficulty.capitalize()}:", True, BLACK)
			screen.blit(diff_text, (50, y_offset))
			y_offset += 40
			
			for i, score in enumerate(scores[difficulty][:5]):
				score_text = SMALL_FONT.render(
					f"{i+1}. Time: {score['time']}s, Mistakes: {score['mistakes']} ({score['date']})", 
					True, BLACK
				)
				screen.blit(score_text, (70, y_offset))
				y_offset += 30
			y_offset += 20
	
	return back_rect

def draw_confirmation():
	overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
	overlay.fill((0, 0, 0, 180))
	screen.blit(overlay, (0, 0))
	
	box_rect = pygame.Rect(SCREEN_WIDTH//4, SCREEN_HEIGHT//3, SCREEN_WIDTH//2, SCREEN_HEIGHT//3)
	pygame.draw.rect(screen, WHITE, box_rect)
	
	text = FONT.render("Quit to menu?", True, BLACK)
	yes_rect = pygame.Rect(SCREEN_WIDTH//4 + 50, SCREEN_HEIGHT//2, 100, 50)
	no_rect = pygame.Rect(SCREEN_WIDTH//4 + 250, SCREEN_HEIGHT//2, 100, 50)
	
	pygame.draw.rect(screen, LIGHT_GREEN, yes_rect)
	pygame.draw.rect(screen, LIGHT_RED, no_rect)
	
	screen.blit(text, (box_rect.centerx - text.get_width()//2, box_rect.y + 30))
	
	yes_text = FONT.render("Yes", True, BLACK)
	no_text = FONT.render("No", True, BLACK)
	
	screen.blit(yes_text, (yes_rect.centerx - yes_text.get_width()//2, yes_rect.centery - yes_text.get_height()//2))
	screen.blit(no_text, (no_rect.centerx - no_text.get_width()//2, no_rect.centery - no_text.get_height()//2))
	
	return yes_rect, no_rect

def get_cell_from_pos(pos):
	x, y = pos
	if x < GRID_OFFSET or x >= GRID_OFFSET + 600 or y < 0 or y >= 600:
		return None
	row = y // CELL_SIZE
	col = (x - GRID_OFFSET) // CELL_SIZE
	return (row, col)

def get_number_from_pos(pos, number_rects):
	x, y = pos
	for i, rect in enumerate(number_rects):
		if rect.collidepoint(x, y):
			return i + 1  # Returns 1-9
	return None

# Game states
MENU = 0
GAME = 1
SCORES = 2

# Initial state
current_state = MENU
game = None
menu_buttons = None
back_button = None
note_mode = False
confirming_quit = False
yes_rect, no_rect = None, None
control_rects = None
number_rects = None

# Game loop
running = True
while running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		
		if event.type == pygame.MOUSEBUTTONDOWN:
			pos = pygame.mouse.get_pos()
			
			if current_state == MENU:
				if menu_buttons:
					easy_rect, medium_rect, hard_rect, scores_rect = menu_buttons
					
					if easy_rect.collidepoint(pos):
						game = Sudoku(difficulty="easy")
						current_state = GAME
						note_mode = False
					elif medium_rect.collidepoint(pos):
						game = Sudoku(difficulty="medium")
						current_state = GAME
						note_mode = False
					elif hard_rect.collidepoint(pos):
						game = Sudoku(difficulty="hard")
						current_state = GAME
						note_mode = False
					elif scores_rect.collidepoint(pos):
						current_state = SCORES
						back_button = draw_scores()
			
			elif current_state == SCORES:
				if back_button and back_button.collidepoint(pos):
					current_state = MENU
			
			elif current_state == GAME:
				if not game.game_over:
					if not confirming_quit:
						cell = get_cell_from_pos(pos)
						if cell:
							if game.board[cell[0]][cell[1]] == 0:
								game.selected = cell
						
						if number_rects:
							num = get_number_from_pos(pos, number_rects)
							if num is not None and game.selected:
								if note_mode:
									game.toggle_note(game.selected[0], game.selected[1], num)
								else:
									game.place_number(game.selected[0], game.selected[1], num)
									game.is_complete()
						
						if control_rects:
							clear_rect, note_rect, undo_rect, menu_rect, _ = control_rects
							
							if clear_rect.collidepoint(pos) and game.selected:
								game.place_number(game.selected[0], game.selected[1], 0)
							elif note_rect.collidepoint(pos):
								note_mode = not note_mode
							elif undo_rect.collidepoint(pos):
								game.undo()
							elif menu_rect.collidepoint(pos):
								confirming_quit = True
					else:
						if yes_rect and yes_rect.collidepoint(pos):
							current_state = MENU
							confirming_quit = False
							note_mode = False
						elif no_rect and no_rect.collidepoint(pos):
							confirming_quit = False
				else:  # Game over screen
					if event.key == pygame.K_r:
						game = Sudoku(difficulty=game.difficulty)
						note_mode = False
					elif event.key == pygame.K_ESCAPE:
						current_state = MENU
		
		if event.type == pygame.KEYDOWN:
			if current_state == GAME:
				if event.key == pygame.K_r:
					game = Sudoku(difficulty=game.difficulty)
					note_mode = False
				elif event.key == pygame.K_ESCAPE:
					if game.game_over:
						current_state = MENU
					else:
						confirming_quit = not confirming_quit
				elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
					if game.selected and game.board[game.selected[0]][game.selected[1]] == 0:
						game.place_number(game.selected[0], game.selected[1], 0)
				elif event.key == pygame.K_n:
					note_mode = not note_mode
				elif event.key == pygame.K_u:
					game.undo()
				elif event.key == pygame.K_m:
					confirming_quit = True
				elif event.key in range(pygame.K_1, pygame.K_9 + 1):
					if game.selected and game.board[game.selected[0]][game.selected[1]] == 0:
						num = event.key - pygame.K_0
						if note_mode:
							game.toggle_note(game.selected[0], game.selected[1], num)
						else:
							game.place_number(game.selected[0], game.selected[1], num)
							game.is_complete()
				elif event.key == pygame.K_UP and game.selected:
					game.selected = (max(0, game.selected[0]-1), game.selected[1])
				elif event.key == pygame.K_DOWN and game.selected:
					game.selected = (min(8, game.selected[0]+1), game.selected[1])
				elif event.key == pygame.K_LEFT and game.selected:
					game.selected = (game.selected[0], max(0, game.selected[1]-1))
				elif event.key == pygame.K_RIGHT and game.selected:
					game.selected = (game.selected[0], min(8, game.selected[1]+1))
			elif current_state in [MENU, SCORES]:
				if event.key == pygame.K_ESCAPE:
					if current_state == SCORES:
						current_state = MENU
					else:
						running = False
	
	if current_state == GAME and game:
		game.update_time()
	
	# Drawing
	if current_state == MENU:
		menu_buttons = draw_menu()
	elif current_state == SCORES:
		back_button = draw_scores()
	elif current_state == GAME and game:
		draw_grid()
		draw_numbers(game.board, game.user_input, game.notes, game.incorrect_cells, game.selected, note_mode)
		control_rects = draw_controls(note_mode)
		if control_rects:
			_, _, _, _, number_rects = control_rects
		
		if confirming_quit:
			yes_rect, no_rect = draw_confirmation()
		
		if game.game_over:
			draw_game_over()
	
	pygame.display.flip()

pygame.quit()
sys.exit()
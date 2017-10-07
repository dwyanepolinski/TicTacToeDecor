#!/usr/bin/env python2.7
# coding=utf8

import gtk
import sys
import cli as cliApp
import gobject
from cStringIO import StringIO
from threading import Thread
from Queue import Queue
from time import sleep

gobject.threads_init()


class Capturing(list):

	def __enter__(self):
		self._stdout = sys.stdout
		sys.stdout = self._stringio = StringIO()
		return self

	def __exit__(self, *args):
		self.extend(self._stringio.getvalue().splitlines())
		del self._stringio
		sys.stdout = self._stdout


class GameGtk():

	def __init__(self):
		self.c = 0
		self.board_fields = []
		self.firstLogin = True
		self.nick = ''
		self.t = None
		self.control_buttons = []
		self.host_game_queue_message = 'tak'
		self.create_window()	


	def destroy(self, widget):
		self.logout()
		gtk.main_quit()


	def start(self):
		gtk.main()


	def create_window(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.connect('destroy', self.destroy)
		self.window.set_title("Gra O vs X")
		self.window.resize(300, 400)
		# log text view
		self.scroll_area = gtk.ScrolledWindow()
		self.scroll_area.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.window_log = gtk.TextView()
		self.window_log.set_editable(False)
		self.add_text('Witaj! Zaloguj się do serwera :)')
		self.scroll_area.add(self.window_log)
		# grid with buttons
		board_layout = gtk.Table(3, 3, True)
		j = 0
		for i in self.grid(9):
			field = gtk.Button(str(1 + i + 3 * j))
			self.board_fields.append(field)
			field.connect("clicked", self.on_field_click)
			field.set_sensitive(False)
			board_layout.attach(field, i, i + 1, j, j + 1)
			if i == 2:
				j += 1
		# control panel buttons
		control_buttons_layout = gtk.Table(1, 3)
		self.session_button = gtk.Button('Zaloguj się')
		first_option_button = gtk.Button('Zakładam')
		second_option_button = gtk.Button('Pokaż gry')
		self.session_button.connect('clicked', self.on_session_click)
		first_option_button.connect('clicked', self.on_option_click)
		second_option_button.connect('clicked', self.on_option_click)
		first_option_button.set_sensitive(False)
		second_option_button.set_sensitive(False)
		control_buttons_layout.attach(self.session_button, 0, 1, 0, 1)
		control_buttons_layout.attach(first_option_button, 1, 2, 0, 1)
		control_buttons_layout.attach(second_option_button, 2, 3, 0, 1)
		# input panel
		input_layout = gtk.Table(2, 1)
		input_label = gtk.Label('Podaj nazwę przeciwnika:')
		input_field_layout = gtk.Table(1, 4)
		input_field = gtk.Entry()
		input_button = gtk.Button('Graj!')
		input_button.connect('clicked', self.on_option_click)
		input_field.set_sensitive(False)
		input_button.set_sensitive(False)
		input_field.set_size_request(30,60)
		input_field_layout.attach(input_field, 0, 3, 0, 1)
		input_field_layout.attach(input_button, 3, 4, 0, 1)
		input_layout.attach(input_label, 0, 1, 0, 1)
		input_layout.attach(input_field_layout, 0, 1, 1, 2)
		# create list with control widgets
		self.control_buttons = [first_option_button, second_option_button, input_field, input_button]
		# attach all to main view
		main_layout = gtk.Table(4, 1, True)
		main_layout.attach(self.scroll_area, 0, 1, 0, 1)
		main_layout.attach(board_layout, 0, 1, 1, 2)
		main_layout.attach(input_layout, 0, 1, 2, 3)
		main_layout.attach(control_buttons_layout, 0, 1, 3, 4)
		self.window.add(main_layout)
		# show all
		self.window.show_all()


	def on_field_click(self, widget):
		self.put_queue_data(widget.get_label())
		for field in self.board_fields:
			field.set_sensitive(False)
		try:
			self.mark_field(int(widget.get_label()) - 1, False)
		except:
			pass


	def on_option_click(self, widget):
		data = ''
		widget_id = widget.get_label()
		if widget_id == 'Zakładam':
			data = self.host_game_queue_message
			self.add_text('Założyłeś grę! Oczekiwanie na gracza...')
			self.control_buttons[1].set_sensitive(False)
			self.session_button.set_sensitive(False)
		if widget_id == 'Pokaż gry':
			data = '@'
		if widget_id == 'Graj!':
			data = self.control_buttons[-2].get_text()
		if widget_id == 'OK':
			self.add_text('Tip: Rozpocznij nową grę lub zobacz dostępne!')
			data = 'ok'
			widget.set_label('Graj!')
			for button in self.control_buttons[:-2]:
				button.set_sensitive(True)
			self.session_button.set_sensitive(True)
			for i in xrange(1, 10):
				self.board_fields[i - 1].set_label(str(i))
				self.board_fields[i - 1].set_sensitive(False)
		self.put_queue_data(data)
		

	def on_session_click(self, widget):
		if widget.get_label() == 'Zaloguj się':
			self.login(widget)
		else:
			self.logout(widget)


	def mark_field(self, number, by_opponent):
		self.board_fields[number].set_label(self.character(self.c if not by_opponent else not self.c))
		self.board_fields[number].set_sensitive(False)


	@staticmethod
	def put_queue_data(data):
		cliApp.q.put(data)
		sleep(0.1)
		sys.stdout.flush()


	def character(self, c):
		return 'x' if c else 'o'


	def opponent_move(self):
		updated_board = [field for field in cliApp.board if field.isdigit()]
		gtk_board = [field.get_label() for field in self.board_fields if field.get_label().isdigit()]
		self.mark_field(int([field for field in gtk_board if field not in updated_board][0]) - 1, True)
		

	def responseToDialog(self, entry, dialog, response):
		dialog.response(response)


	@staticmethod
	def grid(n):
		i = 1
		sub = 0
		while i <= n:
			yield i - sub - 1
			if(i % 3 == 0):
				sub += 3
			i += 1


	def add_text(self, text):
		game_log = self.window_log.get_buffer()
		game_log.insert(game_log.get_end_iter(), '\n' + text + '\n')
		self.window_log.set_buffer(game_log)


	def login(self, widget):
		dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, None)
		dialog.set_markup('Podaj swój <b>nick</b>:')
		entry = gtk.Entry()
		entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label("Nick:"), False, 5, 5)
		hbox.pack_end(entry)
		dialog.format_secondary_markup("Musi byc unikatowy, bez znaków <i>@</i> i <i>:</i>")
		dialog.vbox.pack_end(hbox, True, True, 0)
		dialog.show_all()
		dialog.run()
		self.nick = entry.get_text()
		cliApp.connect()
		cliApp.run_game(widget, self)
		for button in self.control_buttons[:-2]:
			button.set_sensitive(True)
		self.add_text('Tip: Utwórz grę lub wyświetl gry')
		dialog.destroy()


	def logout(self, widget = None):
		for button in self.control_buttons[:-2]:
			button.set_sensitive(False)
		self.nick = ''
		self.firstLogin = True
		if self.t:
			self.put_queue_data(':')
		else:
			try:
				cliApp.client.send('EXIT')
				cliApp.client.close()
			except:
				pass
		if widget:
			widget.set_label('Zaloguj się')
		cliApp.printstatus(False, '', '', 'Pomyślnie wylogowano.')


def play_decorator(func):
	def wrapper(*args):
		cliApp.gtk.c = True if 'FIRST' in args[0] else False
		return func(*args)
	return wrapper


def sync_decorator(func):
	def wrapper(*args):
		func(*args)
		gobject.idle_add(cliApp.gtk.add_text, '')
		cliApp.gtk.opponent_move()
	return wrapper


def list_games_decorator(func):
	def wrapper(*args):
		with Capturing() as output:
			func(*args)
		cliApp.gtk.host_game_queue_message = ''
		cliApp.gtk.add_text('Gry otwarte na serwerze:\n' + '\n'.join(output))
		for button in cliApp.gtk.control_buttons[2:]:
			button.set_sensitive(True if output[0] != 'Brak utworzonych gier' else False)
	return wrapper


def run_game_docorator(func):
	def wrapper(*args):
		widget = args[0]
		if '@' not in cliApp.gtk.nick and ':' not in cliApp.gtk.nick:
			if cliApp.gtk.nick != '':
				if cliApp.gtk.firstLogin:
					cliApp.client.recv(64).strip()
					cliApp.gtk.firstLogin = False
				cliApp.client.send(cliApp.gtk.nick)
				r = cliApp.client.recv(64).strip()
				if r == 'CONNECTED':
					cliApp.printstatus(True, cliApp.gtk.nick, '', 'Zalogowano pomyślnie.')
					widget.set_label('Wyloguj')
					cliApp.q = Queue()
					cliApp.gtk.t = Thread(target = cliApp.start, args=(cliApp.client, ''))
					cliApp.gtk.t.start()
					sleep(0.1)
					sys.stdout.flush()
				else:
					cliApp.gtk.nick=''
					cliApp.printstatus(True, '', '', 'Nick zajęty, spróbuj ponownie.')
		else:
			cliApp.gtk.nick = ''
			cliApp.printstatus(False, '', '', 'Niepoprawna nazwa użytkownika')
	return wrapper


def printstatus_decorator(func):
	def wrapper(connected, nick, opponent, msg):
		nick = (cliApp.gtk.nick if cliApp.gtk.nick!='' else 'niezalogowany')
		output = '\n------------------------------'
		output += '\n| Serwer | Nick | Przeciwnik |'
		output += '\n| %s | %s | %s |' % ('Rozłączono' if connected != True else '127.0.0.1:4444', nick, 'brak' if opponent == '' else opponent)
		output+= '\n[Info]:  %s' % (msg if msg != '' else 'Brak')
		cliApp.gtk.add_text(output)
		if 'Rozpoczęto grę,' in msg:
			cliApp.gtk.session_button.set_sensitive(False)
			for button in cliApp.gtk.control_buttons:
				button.set_sensitive(False)
		if 'Twój ruch' in msg:
			for field in cliApp.gtk.board_fields:
				if field.get_label().isdigit():
					field.set_sensitive(True)
		if 'Gratulacje, wygrałeś!' in msg or 'Niestety, przegrałeś' in msg:
			cliApp.gtk.control_buttons[-1].set_label('OK')
			cliApp.gtk.control_buttons[-1].set_sensitive(True)
		adj = cliApp.gtk.scroll_area.get_vadjustment()
		adj.set_value(adj.get_upper() - adj.get_page_size())
	return wrapper


def queue_input(label):
	print label
	if label == 'Enter - kontynuuj':
		cliApp.gtk.opponent_move()
	return cliApp.q.get()


if __name__ == '__main__':
	cliApp.raw_input = queue_input
	cliApp.gtk = GameGtk()
	cliApp.gtk.start()

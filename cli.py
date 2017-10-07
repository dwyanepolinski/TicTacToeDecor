#!/usr/bin/env python2.7
# coding=utf8
import socket
import sys
import os
from gtkwin import (run_game_docorator, printstatus_decorator, 
					list_games_decorator, sync_decorator, play_decorator)

board = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
client = None

def connect():
	global client
	target_host = "127.0.0.1"
	target_port = 4444
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect((target_host, target_port))


@printstatus_decorator
def printstatus(connected, nick, opponent, error):
	# os.system('cls' if os.name == 'nt' else 'clear')
	print 'Gra sieciowa O&X'
	print '[status serwera: %s' % ('Łączenie z serwerem...]' if connected != True else 'Podłączono][użytkownik: %s]' % nick),
	print '[przeciwnik: %s]' % ('brak' if opponent == '' else opponent)
	print('[Komunikat] %s\n' % error if error != '' else '\n')


def show():
	print '------'
	for i in range(9):
		print board[i],
		if (i + 1) % 3 == 0:
			print '\n'
	print '------\n'


def host_game(client, nick):
	print 'Czekanie na gracza...'
	client.send('HOST_GAME')
	msg = client.recv(64).strip()
	play(msg, client, nick, '')


@list_games_decorator
def list_games(client):
	client.send('LIST')
	glist = client.recv(64).strip().strip('@').split('|')[1:]
	glist = filter(None, glist)
	if len(glist) == 0:
		print 'Brak utworzonych gier'
	else:
		j = 1
		for i in glist:
			print '[%d] %s' % (j, i)
			j += 1


def move(client, opponent, zn):
	printstatus(True, nick, opponent, 'Twój ruch')
	show()
	while True:
		position = raw_input('Podaj pozycję w jakiej umieścisz %s:' % zn)
		if position.isdigit() and int(position) - 1 in range(9) and board[int(position) - 1].isdigit():
			board[int(position) - 1] = zn
			client.send(str(int(position) - 1) + ':' + opponent)
			break
		else:
			print 'Zła podana pozycja, spróbuj jeszcze raz'
	printstatus(True, nick, opponent, 'Ruch przeciwnika...')
	show()


@sync_decorator
def sync(client, opponent, zn):
	msg = client.recv(64).strip()
	if msg == 'STOP':
		start(client, 'Gra została przerwana, przeciwnik oszukiwał')
	elif msg.isdigit():
		board[int(msg)] = ('x' if zn == 'o' else 'o')
	else:
		if 'LOSE' in msg:
			board[int(msg.replace('LOSE', ''))] = ('x' if zn == 'o' else 'o')
		printstatus(True, nick, opponent, ('Gratulacje, wygrałeś!' if msg ==
										   'WIN' else 'Remis!' if msg == 'DRAW' else 'Niestety, przegrałeś'))
		show()
		raw_input('Enter - kontynuuj')
		for i in range(9):
			board[i] = str(i + 1)
		start(client, '')


@play_decorator
def play(msg, client, nick, opponent):
	if 'FIRST' in msg:
		zn = 'x'
		s = True
	else:
		zn = 'o'
		s = False
	if opponent == '':
		opponent = msg.partition('@')[2]
	printstatus(True, nick, opponent, 'Rozpoczęto grę, ' +
				('zaczynasz' if zn == 'x' else 'przeciwnik zaczyna'))
	while True:
		if s:
			move(client, opponent, zn)
			s = False
		sync(client, opponent, zn)
		move(client, opponent, zn)
	print 'DONE'


def start(client, error):
	inp = raw_input(
		'Zakładasz grę czy dołączasz do gry? \n(\'tak\' - zakładam/Enter - nie zakładam/\':\' - wyjscie) :')
	if inp == 'tak':
		host_game(client, nick)
	elif inp == ':':
		client.send('EXIT')
		sys.exit('Pomyślnie rozłączono z serwerem. Bye')
	else:
		while True:
			printstatus(True, nick, '', error)
			print 'Użytkownicy udostępniający grę:'
			while True:
				list_games(client)
				opponent = raw_input(
					'Podaj nik gracza z jakim chcesz zagrać, listuj gry ponownie lub załóż grę \n(podaj nick/\'@\' - listuj/załóż - Enter/\':\' - wyjście) :')
				if opponent == ':':
					client.send('EXIT')
					sys.exit('Pomyślnie rozłączono z serwerem. Bye')
				if opponent != '@':
					break
			if opponent == '':
				host_game(client, nick)
				break
			else:
				client.send('@' + opponent)
				msg = client.recv(64).strip()
				if 'PLAY' in msg:
					play(msg, client, nick, opponent)
					break
				else:
					error = 'Brak takiego użytkownika!'


@run_game_docorator
def run_game():
	printstatus(False, '', '', '')
	msg = client.recv(64).strip()
	while msg != 'CONNECTED':
		print('Użytkownik istnieje! ' if msg == 'EXIST!NICK?' else 'Witaj!')
		nick = ''
		while nick == '':
			nick = raw_input('Podaj swoją nazwę użytkownika: ')
		client.send(nick)
		msg = client.recv(64).strip()

	printstatus(True, nick, '', '')
	start(client, '')

if __name__ == '__main__':
	connect()
	run_game()
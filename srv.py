#!/usr/bin/env python2.7
#coding=utf8
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
import random

nicks={}
busy={}
games={}
boards={}

def analyze(board,c):
	result='PLAY'
	for i in (0,1,2):
		if (board[0+(3*i)]==c)and(board[1+(3*i)]==c)and(board[2+(3*i)]==c):
			result='WIN'
		if (board[0+i]==c)and(board[3+i]==c)and(board[6+i]==c):
			result='WIN'
	if (board[0]==c)and(board[4]==c)and(board[8]==c):
			result='WIN'
	if (board[2]==c)and(board[4]==c)and(board[6]==c):
			result='WIN'
	if (result=='PLAY') and (''.join(board).isalpha()):
		result='DRAW'
	return result

def disc_user (cli,nick):
	cli.close()
	del busy[nick]
	del nicks[nick]
	try:
		del games[nick]
	except KeyError:
		pass
	to_del=''
	for i in (i for i in boards if nick in i):
		to_del=i
		free_client=i.replace(nick,'').strip('|')
	if to_del!='':
		del boards[to_del]
	print 'Odłączono klienta : %s' % nick

def ban_user(cli,nick,opponent):
	to_del=''
	for i in (i for i in boards if nick in i):
		to_del=i
		free_client=i.replace(nick,'').strip('|')
	if to_del!='':
		del boards[to_del]
	busy[free_client]=False
	games[free_client]=False
	nicks[free_client].send('STOP')
	del busy[nick]
	del games[nick]
	del nicks[nick]
	cli.send('BANNED')
	cli.close()
	print 'Zbanowano klienta : %s' % nick

def check(cli,index,position,zn,nick,opponent):
	boards[index][position]=zn
	result=analyze(boards[index],zn)
	if result!='PLAY':
		print ('remis' if result=='DRAW' else 'Użytkownick %s wygrywa, %s przegrywa - koniec gry'%(nick,opponent))
		del boards[index]
		games[nick]=False
		games[opponent]=False
		busy[nick]=False
		busy[opponent]=False
		cli.send('WIN' if result!='DRAW' else result)
		nicks[opponent].send('LOSE'+str(position))
	else:
		nicks[opponent].send(str(position))

def connection(cli):
	while True:
		cli.send('NICK?')
		nick=cli.recv(64).strip()
		print 'Logowanie --> \'%s\''%nick if nick != '' else 'Odłączono klienta [niezalogowany]'
		if nick in nicks:
			cli.send('EXIST!')
		elif nick=='':
			cli.close()
			exit()
		elif ':' in nick or '@' in nick or '|' in nick:
			cli.send('ERROR!')
		else:
			cli.send('CONNECTED')
			print 'Podłączono klienta : %s' % nick 
			nicks[nick]=cli
			busy[nick]=False
			games[nick]=False
			break
	while True:
		recv_msg=cli.recv(64).strip().strip()
		print 'Odebrano \'%s\''%recv_msg
		
		#LIST
		if recv_msg=='LIST' and games[nick]==False:
			cli.send('@|'+'|'.join(i for i in nicks if busy[i]==False and games[i]==True))
		
		#BLANK
		elif recv_msg=='':
			disc_user(cli,nick)
			break
		
		#EXIT
		elif recv_msg=='EXIT':
			disc_user(cli,nick)
			break
		
		#HOST_GAME
		elif recv_msg=='HOST_GAME':
				games[nick]=True
				print 'Użytkownik %s tworzy grę' % nick
		
		#START_GAME
		elif recv_msg[0]=='@' and games[nick]==False:
			opponent=recv_msg[1:]
			if opponent not in (i for i in nicks if busy[i]==False and games[i]==True) or opponent==nick:
				cli.send('USERNAME_ERROR')
			else:
				print 'Użytkownik %s dołącza do gry użytkownika %s' % (nick,opponent)
				busy[opponent]=True
				busy[nick]=True
				r=random.getrandbits(1)
				cli.send('PLAY_FIRST' if r==1 else 'PLAY_SECOND')
				nicks[opponent].send('PLAY_FIRST@'+nick if (1-r)==1 else 'PLAY_SECOND@'+nick)
				boards[nick+'|'+opponent]=['1','2','3','4','5','6','7','8','9',(nick if r==1 else opponent)]
		
		#MAKE_MOVE
		elif recv_msg[0].isdigit() and int(recv_msg[0]) in range(9):
			print 'Wykonuję ruch'
			position=int(recv_msg[0])
			opponent=recv_msg.partition(':')[2]
			if nick+'|'+opponent not in boards and opponent+'|'+nick not in boards:
				ban_user(cli,nick,opponent)
				break;
			try:
				if boards[nick+'|'+opponent][position].isalpha():
					ban_user(cli,nick,opponent)
					break;
				check(cli,nick+'|'+opponent,position,('x' if boards[nick+'|'+opponent][-1]==nick else 'o'),nick,opponent)
			except KeyError:
				if boards[opponent+'|'+nick][position].isalpha():
					ban_user(cli,nick,opponent)
					break;
				check(cli,opponent+'|'+nick,position,('x' if boards[opponent+'|'+nick][-1]==nick else 'o'),nick,opponent)
		#WRONG_COMMAND
		else:
			cli.send('SYNTAX_ERROR')

print '\n\n\n---------------------------'
print 'Serwer gry kólko i krzyżyk'
print '---------------------------'

s=socket()
s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
s.bind(('',4444))
s.listen(1)

while True:
	cli,adr=s.accept()
	Thread(target=connection,args=(cli,)).start()



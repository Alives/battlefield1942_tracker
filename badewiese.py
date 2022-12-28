#!/usr/bin/python3

import socket
import time

from datetime import timedelta
from itertools import zip_longest


PADDING = 4
PORT = 23000
SEP = ': '
SERVER = '78.46.52.115'
TERM = {
    'bright_white_bg': '\033[107;30m',
    'clear_screen': '\033c',
    'reset': '\033[0m',
    'underline': '\033[4m',
}


def connect():
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.settimeout(3)
  sock.connect((SERVER, PORT))
  return sock


def query(query, sock):
  sock.send(bytes('\\' + query + '\\', encoding='ascii'))
  response = sock.recv(16384).decode('ISO-8859-1')
  data = {}
  op = ': '
  prev = ''
  for entry in response[1:].split('\\'):
    if op == ': ':
      op = ''
    elif not op:
      data[prev] = entry
      op = ': '
    prev = entry
  return data


def get_status(sock):
  status = query('status', sock)
  tickets = {k: f'Team {k} ({status["tickets" + k]})' for k in '12'}
  hostname = status['hostname']
  mapname = status['mapname'].title()
  time_left = str(
      timedelta(seconds=int(status['roundTimeRemain']))).lstrip('0:')
  header = ' : '.join([hostname, mapname, time_left])
  return header, tickets


def get_players(sock):
  data = query('players', sock)
  player_dict = {'1': {}, '2': {}}
  player_list = {'1': [], '2': []}

  for num in range(129):
    try:
      name = data[f'playername_{num}'].strip()
      score = data[f'score_{num}']
      team = data[f'team_{num}']
    except KeyError:
      break
    if name in player_dict[team]:
      player_dict[team][name] = max(int(score), int(player_dict[team][name]))
    else:
      player_dict[team][name] = int(score)

  for team, scores in player_dict.items():
    player_list[team] = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    player_list[team] = [(n, str(s)) for n, s in player_list[team]]
  return player_list


def get_width(tickets, players):
  width_name = 0
  width_score = 0
  for roster in list(players.values()):
    for name, score in roster:
      width_name = max(width_name, len(name))
      width_score = max(width_score, len(score))
  width_tickets = max([len(x) for x in list(tickets.values())])
  return max((width_name + len(SEP) + width_score), width_tickets)


def print_header(header, tickets, width):
  fmt = lambda f, s: TERM[f] + s + TERM['reset']
  tix = [tickets[k].ljust(width) for k in '12']
  gap = ' ' * max(round((len(header) - len(''.join(tix))) / 3), PADDING)
  header_pad = (width * 2) + (len(gap) * 3)
  print(fmt('bright_white_bg', header.center(header_pad)))
  print()
  print(gap + fmt('underline', tix[0]) + gap + fmt('underline', tix[1]))
  return gap


def output(header, tickets, players):
  width = get_width(tickets, players)
  gap = print_header(header, tickets, width)

  for entries in zip_longest(*players.values()):
    print(gap, end='')
    for num, player in enumerate(entries):
      if player:
        name, score = player
        padding = ' ' * (width - (len(name + SEP + score)))
        print(name + SEP + padding + score, end='')
      else:
        print(' ' * width,  end='')
      if num == 0:
        print(gap, end='')
    print()


errors = []
print(TERM['clear_screen'], end='')
while True:
  try:
    sock = connect()
    header, tickets = get_status(sock)
    players = get_players(sock)
    output(header, tickets, players)
    errors = []
  except (ConnectionRefusedError, TimeoutError) as e:
    sock.close()
    errors.append(str(e))
  if errors:
    print('\n'.join(errors))
  time.sleep(1)
  print(TERM['clear_screen'], end='')

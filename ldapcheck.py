#!/usr/bin/env python

import ldap
from sys import exit
from argparse import ArgumentParser


def parseargs():
    p = ArgumentParser()
    p.add_argument('-s', '--server', required = True)
    p.add_argument('-p', '--port', required = True, type = int, default = 389)
    p.add_argument('-b', '--basedn', required = True)
    p.add_argument('--filter')
    p.add_argument('--username')
    p.add_argument('--password')
    p.add_argument('--secure', action = 'store_true')
    p.add_argument('-t', '--timeout', type = int, default = 5)
    p.add_argument('-v', '--verbose', action = 'store_true')
    return vars(p.parse_args())

class LdapConnect():
  """ldap connection wrapper"""
	def __init__(self, server, port, basedn, user, passwd, timeout, secure = False):
		self.server, self.port = server, port
		self.basedn, self.secure = basedn, secure
		if user == None or passwd == None:
		    self.user, self.passwd = '', ''
		else:
			self.user, self.passwd = user, passwd
		self.search_scope = ldap.SCOPE_SUBTREE

	def __del__(self):
		if self.ld:
			self.ld.unbind()

	def _connect(self):
		try:
			if not self.secure:
				self.ld = ldap.initialize("ldap://%s:%s" % (self.server, self.port))
			else:
				self.ld = ldap.initialize("ldaps://%s:%s" % (self.server, self.port))
		except ldap.LDAPError, e:
			print 'Cannot connect, %s' % e
			exit(1)
		self.ld.set_option = (ldap.OPT_DEBUG_LEVEL, 100)
		self.ld.set_option = (ldap.OPT_NETWORK_TIMEOUT, 5)

	def _bind(self):
		self._connect()
		try:
			self.ld.simple_bind_s(who = self.user, cred = self.passwd)
		except ldap.INVALID_CREDENTIALS:
			print 'Invalid credentials'
			exit(2)

	def search(self, filter, verbose = False):
		self._bind()
		try:
			rows = self.ld.search_s(self.basedn, self.search_scope, filter)
		except TypeError:
			print '--filter <filter> is required'
			exit(3)
		if verbose:
			for row in rows:
				print row
		exit(0)


def main():
	conn = LdapConnect(server = params['server'], port = params['port'], timeout = params['timeout'],
		basedn = params['basedn'], user = params['username'], passwd = params['password'])
	conn.search(params['filter'], params['verbose'])


if __name__ == '__main__':
	params = parseargs()
	main()

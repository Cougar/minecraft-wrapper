# -*- coding: utf-8 -*-
import socket, datetime, time, sys, threading, random, subprocess, os, json, signal, traceback, ConfigParser, ast
from log import *
from config import Config
from irc import IRC
from server import Server
from importlib import import_module
import importlib
from api import API
from proxy import Proxy
from web import Web
			
class Wrapper:
	def __init__(self):
		self.log = Log()
		self.halt = False
		self.configManager = Config(self.log)
		self.plugins = {}
		self.server = False
		self.proxy = Proxy(self)
		self.listeners = []
		
		self.commands = {}
		self.events = {}
		
		self.api = API(self, "Wrapper.py")
		self.api.registerCommand("ponk", self.ponk)
	def ponk(self, player, args):
		player.message("&aHey man, you just ran ponk! That's cool!")
	def loadPlugin(self, i):
		self.log.info("Loading plugin %s..." % i)
		if os.path.isdir("wrapper-plugins/%s" % i):
			plugin = import_module(i)
			name = i
		elif i[-3:] == ".py":
			plugin = import_module(i[:-3])
			name = i[:-3]
		else:
			return False
		self.commands[name] = {}
		self.events[name] = {}
		main = plugin.Main(API(self, name), PluginLog(self.log, name))
		self.plugins[name] = {"main": main, "name": name, "good": True, "module": plugin} #  "events": {}, "commands": {}, 
		main.onEnable()
	def unloadPlugin(self, plugin):
		del self.commands[plugin]
		del self.events[plugin]
		self.plugins[plugin]["main"].onDisable()
		reload(self.plugins[plugin]["module"])
	def loadPlugins(self):
		self.log.info("Loading plugins...")
		if not os.path.exists("wrapper-plugins"):
			os.mkdir("wrapper-plugins")
		sys.path.append("wrapper-plugins")
		for i in os.listdir("wrapper-plugins"):
			try:
				if os.path.isdir("wrapper-plugins/%s" % i): self.loadPlugin(i)
				elif i[-3:] == ".py": self.loadPlugin(i)
			except:
				for line in traceback.format_exc().split("\n"):
					self.log.debug(line)
				self.log.error("Failed to import plugin '%s'" % i)
				self.plugins[i] = {"name": i, "good": False}
		self.callEvent("helloworld.event", {"testValue": True})
	def reloadPlugins(self):
		for i in self.plugins:
			try:
				self.unloadPlugin(i)
			except:
				for line in traceback.format_exc().split("\n"):
					self.log.debug(line)
				self.log.error("Failed to unload plugin '%s'" % i)
		self.plugins = {}
		self.loadPlugins()
		self.log.info("Plugins reloaded")
	def callEvent(self, event, payload):
		if event == "player.runCommand":
			if not self.playerCommand(payload): return False
		for sock in self.listeners:
			sock.append({"event": event, "payload": payload})
		for pluginID in self.events:
			if event in self.events[pluginID]:
				try:
					result = self.events[pluginID][event](payload)
					if result == False:
						return False
				except:
					self.log.error("Plugin '%s' errored out when executing callback event '%s':" % (pluginID, event))
					for line in traceback.format_exc().split("\n"):
						self.log.error(line)
		return True
	def playerCommand(self, payload):
		self.log.info("%s executed '/%s %s'" % (payload["player"], payload["command"], " ".join(payload["args"])))
		if payload["command"] == "wrapper":
			return False
		if payload["command"] == "reload":
			self.reloadPlugins()
			self.api.minecraft.getPlayer(payload["player"]).message({"text": "Plugins reloaded.", "color": "green"})
			return False
		for pluginID in self.plugins:
			plugin = self.plugins[pluginID]
			if not plugin["good"]: continue
			command = payload["command"]
			if command in self.commands[pluginID]:
				try:
					self.commands[pluginID][command](self.api.minecraft.getPlayer(payload["player"]), payload["args"])
					return False
				except:
					self.log.error("Plugin '%s' errored out when executing command: '<%s> /%s':" % (pluginID, payload["player"], command))
					for line in traceback.format_exc().split("\n"):
						self.log.error(line)
					self.api.minecraft.getPlayer(payload["player"]).message({"text": "An internal error occurred on the server side while trying to execute this command. Apologies.", "color": "red"})
					return False
		return True
	def getUUID(self, name):
		f = open("usercache.json", "r")
		data = json.loads(f.read())
		f.close()
		for u in data:
			if u["name"] == name:
				return u["uuid"]
		return False
	def start(self):
		self.configManager.loadConfig()
		self.config = self.configManager.config
		signal.signal(signal.SIGINT, self.SIGINT)
		
		self.loadPlugins()
		
		self.server = Server(sys.argv, self.log, self.configManager.config, self)
		
		if self.config["IRC"]["enabled"]:
			self.irc = IRC(self.server, self.config, self.log, self, self.config["IRC"]["server"], self.config["IRC"]["port"], self.config["IRC"]["nick"], self.config["IRC"]["channels"])
			t = threading.Thread(target=self.irc.init, args=())
			t.daemon = True
			t.start()
		#if self.config["Web"]["enabled"]:
#			self.web = Web(self)
#			t = threading.Thread(target=self.web.wrap, args=())
#			t.daemon = True
#			t.start()
		
		if len(sys.argv) < 2:
			wrapper.server.serverArgs = wrapper.configManager.config["General"]["command"].split(" ")
		else:
			wrapper.server.serverArgs = sys.argv[1:]
		
		captureThread = threading.Thread(target=self.server.capture, args=())
		captureThread.daemon = True
		captureThread.start()
		consoleDaemon = threading.Thread(target=self.console, args=())
		consoleDaemon.daemon = True
		consoleDaemon.start()
		if self.config["Proxy"]["enabled"]:
			proxyThread = threading.Thread(target=self.proxy.host, args=())
			proxyThread.daemon = True
			proxyThread.start()
		
		self.server.startServer()
	def SIGINT(self, s, f):
		self.shutdown()
	def shutdown(self):
		self.halt = True
		sys.exit(0)
	def console(self):
		while not self.halt:
			input = raw_input("")
			if len(input) < 1: continue
			if input[0] is not "/": 
				try:
					self.server.run(input)
				except:
					break
				continue
			def args(i): 
				try: return input[1:].split(" ")[i];
				except:pass;
			command = args(0)
			if command == "halt":
				self.server.run("stop")
				self.halt = True
				sys.exit()
			elif command == "stop":
				self.server.run("stop")
				self.server.start = False
			elif command == "start":
				self.server.start = True
			elif command == "restart":
				self.server.run("stop")
			elif command == "reload":
				self.reloadPlugins()
			elif command == "plugins":
				self.log.info("List of plugins installed:")
				for plug in self.plugins:
					try: description = self.plugins[plug]["main"].description
					except: description = "No description available for this plugin"
					
					try: version = self.plugins[plug]["main"].version
					except: version = (1, 0, 0)
						
					self.log.info("%s v%s - %s" % (plug, ".".join([str(_) for _ in version]), description))
			elif command == "help":
				self.log.info("/reload - reload plugins")	
				self.log.info("/plugins - lists plugins")	
				self.log.info("/start & /stop - start and stop the server without auto-restarting respectively without shutting down Wrapper.py")
				self.log.info("/restart - restarts the server, obviously")				
				self.log.info("/halt - shutdown Wrapper.py completely")
				self.log.info("Wrapper.py version %s" % Config.version)
			else:
				self.log.error("Invalid command %s" % command)
if __name__ == "__main__":
	wrapper = Wrapper()
	log = wrapper.log
	log.info("Wrapper.py started - version %s" % Config.version)
	
	try:
		t = threading.Thread(target=wrapper.start(), args=())
		t.daemon = True
		t.start()
	except SystemExit:
		#log.error("Wrapper.py received SystemExit")
		wrapper.halt = True
		try:
			for player in wrapper.server.players:
				wrapper.server.run("kick %s Wrapper.py received shutdown signal - bye" % player)
			time.sleep(0.2)
			wrapper.server.run("save-all")
			wrapper.server.run("stop")
		except:
			pass
	except:
		log.error("Wrapper.py crashed - stopping sever to be safe")
		for line in traceback.format_exc().split("\n"):
			log.error(line)
		wrapper.halt = True
		try:
			for player in wrapper.server.players:
				wrapper.server.run("kick %s Wrapper.py crashed - please contact a server admin instantly" % player)
			wrapper.server.run("save-all")
			wrapper.server.run("stop")
		except:
			pass
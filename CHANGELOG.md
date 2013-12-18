#Changelog#

<h4>To-do List</h4>
- Web interface for server management
- Multi-server mode
- Proxy system (like Bungeecord, perhaps)
<ul>
<li> Maybe add some in-game Wrapper.py commands such as /halt</li>
<li> Block/Action Logging</li>
</ul>
- Ability to halt server without shutting down wrapper - for fine server control
- Potentially implement region fixer in wrapper.py
- Update version of Minecraft server automatically
- First-run setup wizard (what is this, Windows 95!? :P)
- Potentially implement a way to reload the config - but that might be too difficult/bug prone
- Clean up & organize code... it's a tad cluttery right now!

<h4>0.4.1</h4>
- Fixed m's being stripped from messages
- Fixed /halt not shutting down Wrapper.py

<h4>0.4.0</h4>
Small update, but brings one much-needed change: the new configuration file system. Change your settings in wrapper.properties now. Much nicer and update-friendly.
- Achivements are announced in IRC
- IRC bridge can be turned off so Wrapper.py can be used as a backup-only script
- New configuration file
- Obstruct usernames in IRC to refrain from pinging (currently doesn't work with colored names, known bug)
- Bug fixes:
<ul>
<li> Save-off during backup</li>
<li> Various crashes, such as when it can't connect to IRC</li>
<li> Other small fixes</li>
</ul>
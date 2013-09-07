SteamAPI
========

An object-oriented Python library for accessing the Steam Web API.

## What's this?
It's a Python library for accessing Steam's [Web API](http://steamcommunity.com/dev), which separates the JSON, HTTP requests, authentication and other web junk from your Python code. Your code will still ask the Steam Web API for bits and bobs of user profiles, games, etc., but invisibly, lazily, and in a cached manner.

It's super-easy to use, straightforward and designed for continuous use. Finally, an easy way to interface with Steam!

## How?
With some abstraction, Pythonic classes and ~~magic~~ tricks. Essentially, I use [*requests*](/kennethreitz/requests) for the actual communication, a few converter classes for parsing the output and making it a proper object, and some well-timed caching to make sure lazy-initialization doesn't get you down.

## Wait, how do I use this fabulous product?
Like so!
```python
>>> import steamapi
>>> steamapi.core.APIConnection(api_key="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
>>> steamapi.user.SteamUser(12345678901234567890)
<SteamUser "Johnny" (12345678901234567890)>
>>> me = _
>>> me.level
15
>>> me.friends
[<SteamUser "Ryan" (9876543210987654321)>, <SteamUser "Tyler" (1234876598762345)>, ...]
```

Or maybe even like this!
```python
...
>>> me.recently_played
[<SteamApp "Dishonored" (205100)>, <SteamApp "Saints Row: The Third" (55230)>, ...]
```

But wait, there's more!
```python
...
>>> me.games
[<SteamApp "Counter-Strike: Source" (240)>, <SteamApp "Team Fortress Classic" (20)>, <SteamApp "Half-Life: Opposing Force" (50)>, ...]
```
And yes, that would be *your entire games library*.

The library was made for both easy use *and* easy prototyping. It supports auto-completion in IPython and other standards-abiding interpreters, even with dynamic objects (APIResponse). I mean, what good is an API if you constantly have to have the documentation, a browser and a *web debugger* open to figure it out?

Note that you need an API key for most commands, **but** API keys can be obtained immediately, for free, from the [Steam Web API developer page](http://steamcommunity.com/dev).

Don't be alarmed by its request for a domain; at this time of writing, the API also **does not** enforce which domain uses the key, so you can experiment freely.

## The API says I can get <???> but I can't find the option for that here! :(
Whoa whoa, easy there, this is still a work in progress. Don't worry though, I plan to have the entire public API mapped & available soon!

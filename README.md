SteamAPI [![Build Status](https://travis-ci.org/smiley/steamapi.svg?branch=master)](https://travis-ci.org/smiley/steamapi)
========
An object-oriented Python 2.7+/3.5+ library for accessing the Steam Web API.

## What's this?
It's a Python library for accessing Steam's [Web API](http://steamcommunity.com/dev), which separates the JSON, HTTP requests, authentication and other web junk from your Python code. Your code will still ask the Steam Web API for bits and bobs of user profiles, games, etc., but invisibly, lazily, and in a cached manner.

It's super-easy to use, straightforward and designed for continuous use. Finally, an easy way to interface with Steam!

## How?
With some abstraction, Pythonic classes and ~~magic~~ tricks. Essentially, I use [*requests*](//github.com/kennethreitz/requests) for the actual communication, a few converter classes for parsing the output and making it a proper object, and some well-timed caching to make sure lazy-initialization doesn't get you down.

## How do I use this?
Clone the repository & run `python setup.py develop`. (Or [download](/smiley/steamapi/archive/master.zip) it & run `python setup.py install`, which copies the code to your local Python packages folder)

Then, you can use it like this:
```python
>>> import steamapi
>>> steamapi.core.APIConnection(api_key="ABCDEFGHIJKLMNOPQRSTUVWXYZ", validate_key=True)  # <-- Insert API key here
>>> steamapi.user.SteamUser(userurl="smileybarry")  # For http://steamcommunity.com/id/smileybarry
Or:
>>> steamapi.user.SteamUser(76561197996416028)  # Using the 64-bit Steam user ID
<SteamUser "Smiley" (76561197996416028)>
>>> me = _
>>> me.level
22
>>> me.friends
[<SteamUser "Bill" (9876543210987654321)>, <SteamUser "Ted" (1234876598762345)>, ...]
```

Or maybe even like this:
```python
...
>>> me.recently_played
[<SteamApp "Dishonored" (205100)>, <SteamApp "Saints Row: The Third" (55230)>, ...]
>>> me.games
[<SteamApp "Counter-Strike: Source" (240)>, <SteamApp "Team Fortress Classic" (20)>, <SteamApp "Half-Life: Opposing Force" (50)>, ...]
```

## More examples
### [Flask](http://flask.pocoo.org/)-based web service
How about [a Flask web service that tells a user how many games & friends he has?](/smiley/steamapi-flask-example)

```python
from flask import Flask, render_template
from steamapi import core, user

app = Flask("Steamer")
core.APIConnection(api_key="YOURKEYHERE")

@app.route('/user/<name>')
def hello(name=None):
  try:
    try:
      steam_user = user.SteamUser(userid=int(name))
    except ValueError: # Not an ID, but a vanity URL.
      steam_user = user.SteamUser(userurl=name)
    name = steam_user.name
    content = "Your real name is {0}. You have {1} friends and {2} games.".format(steam_user.real_name,
                                                                                  len(steam_user.friends),
                                                                                  len(steam_user.games))
    img = steam_user.avatar
    return render_template('hello.html', name=name, content=content, img=img)
  except Exception as ex:
    # We might not have permission to the user's friends list or games, so just carry on with a blank message.
    return render_template('hello.html', name=name)
  
if __name__ == '__main__':
  app.run()
```
*(`hello.html` can be found [here](//github.com/smiley/steamapi-flask-example/blob/master/templates/hello.html))*

You can [try it out for yourself](//github.com/smiley/steamapi-flask-example) by cloning/downloading a ZIP and [deploying it to Google App Engine](https://cloud.google.com/appengine/docs/python/tools/uploadinganapp?hl=en) for free.

---

The library was made for both easy use *and* easy prototyping. It supports auto-completion in IPython and other standards-abiding interpreters, even with dynamic objects (APIResponse). I mean, what good is an API if you constantly have to have the documentation, a browser and a *web debugger* open to figure it out?

Note that you need an API key for most commands, **but** API keys can be obtained immediately, for free, from the [Steam Web API developer page](http://steamcommunity.com/dev).

The API registration page requires a domain, but it's only a formality. It's not enforced by the API server.

## FAQ
*Don't see your question here? More questions were [asked](/../../issues?q=is%3Aissue+label%3Aquestion) and [answered](/../../issues?q=is%3Aissue+label%3Aquestion-answered) in the "Issues" section.*

### Does this work?
Yep! You can try the examples above, or you can just jump in and browse the API using an interpreter. I recommend [IPython](http://ipython.org); it has some awesome auto-completion, search & code inspection.

### How can I get \* using the API? I can't find it here.
You can open a Python interpreter and play around with the library. It's suited for experimentation and prototyping, to help prevent these exact cases. A full documentation will be available soon.

If you still can't find it, I might've not implemented it yet. This is still a work in progress. Don't worry though, I plan to have the entire public API mapped & available soon!

### I have a feature/change that I think should go in. How can I participate?
You can do one of two things:
 1. [Fork the repository](/../../fork) and make your changes. When you're done, send me a pull request and I'll look at it.
 2. [Open a ticket](/../../issues/new) and tell me about it. My aim is to create the best API library in terms of comfort, flexibility and capabilities, and I can't do that alone. I'd love to hear about your ideas.

### Is this official?
No, and it's also not endorsed in any way by Valve Corporation. _(obligatory legal notice)_ I couldn't find a fitting name at this point for it, so I just skipped it for now.

### Can I use this library in my busy web app?
No, but feel free to experiment with it. It's roughly stable right now, with many of the quirks fixed and most classes having a steady API. Small refactorings are rare, and I do plan to overhaul the object system to allow async/batching behaviour, but that's still a way off.

### Is this still actively-developed? The last commit is quite a while ago!
Sadly, not anymore. This isn't abandoned or archived but, as you can tell, I haven't touched it in years. I've moved on and the projects I had in mind for this library (and the reason I wrote it) are dead at this point. If you'd like to add or change things, you can fork the repository and open a pull request, despite the above I can still review and accept changes.

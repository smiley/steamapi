SteamAPI [![Build Status](https://travis-ci.org/smiley/steamapi.png?branch=master)](https://travis-ci.org/smiley/steamapi)
========
An object-oriented Python 2.7+ library for accessing the Steam Web API.

## What's this?
It's a Python library for accessing Steam's [Web API](http://steamcommunity.com/dev), which separates the JSON, HTTP requests, authentication and other web junk from your Python code. Your code will still ask the Steam Web API for bits and bobs of user profiles, games, etc., but invisibly, lazily, and in a cached manner.

It's super-easy to use, straightforward and designed for continuous use. Finally, an easy way to interface with Steam!

## How?
With some abstraction, Pythonic classes and ~~magic~~ tricks. Essentially, I use [*requests*](/kennethreitz/requests) for the actual communication, a few converter classes for parsing the output and making it a proper object, and some well-timed caching to make sure lazy-initialization doesn't get you down.

## How do I use this?
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
>>> me.games
[<SteamApp "Counter-Strike: Source" (240)>, <SteamApp "Team Fortress Classic" (20)>, <SteamApp "Half-Life: Opposing Force" (50)>, ...]
```
And yes, that would be *your entire games library*.

## More examples
### [Flask](http://flask.pocoo.org/)-based web service
How about a Flask web service that tells a user how many games & friends he has?
```python
from flask import Flask
from flask import render_template
from steamapi import * # All submodules.

app = Flask(__name__.split('.')[0])

@app.route('/user/<name>')
def hello(name=None):
  try:
    core.APIConnection(api_key="YOURKEYHERE")
    try:
      steam_user = user.SteamUser(userid=int(name))
    except ValueError: # Not an ID, but a vanity URL.
      steam_user = user.SteamUser(userurl=name)
    name = steam_user.name
    content = "Your real name is {0}. You have {1} friends and {2} games.".format(steam_user.real_name,
                                                                                  len(steam_user.friends),
                                                                                  len(steam_user.games))
    img = steam_user.avatar
  except Exception as ex:
    import pdb
    pdb.set_trace()
    # We might not have permission to the user's friends list or games, so just carry on with a blank message.
    content = None
    img = None
  return render_template('hello.html', name=name, content=content, img=img)
  
if __name__ == '__main__':
  app.run()
```

(And "hello.html": )
```html
<!doctype html>
<html>
  <body>
    <title>Hello there!</title>
    {% if name %}
      <h1>Hello {% if img %}<img src="{{ img }}" /> {% endif %}{{ name }}!</h1>
    {% else %}
      <h1>Hello Anonymous!</h1>
    {% endif %}
    {% if content %}
      <p>{{ content }}</p>
    {% endif %}
  </body>
</html>
```

Wanna try it out for yourself? I deployed it to a [Google App Engine instance](http://smileybarry-example.appspot.com/user/smileybarry). Exactly the same code. (Except I used my key instead of "YOURKEYHERE")

(This is based off of [*Google App Engine's* Python + Flask example](https://developers.google.com/appengine/))

---

The library was made for both easy use *and* easy prototyping. It supports auto-completion in IPython and other standards-abiding interpreters, even with dynamic objects (APIResponse). I mean, what good is an API if you constantly have to have the documentation, a browser and a *web debugger* open to figure it out?

Note that you need an API key for most commands, **but** API keys can be obtained immediately, for free, from the [Steam Web API developer page](http://steamcommunity.com/dev).

Don't be alarmed by its request for a domain; at this time of writing, the API also **does not** enforce which domain uses the key, so you can experiment freely.

## FAQ
### Does this work?
Hell yeah! You can give the examples up above a shot and see for yourself, or you can just jump in and browse the API using an interpreter. I recommend [IPython](http://ipython.org), it has some awesome auto-completion, search & code inspection.

### How can I get * using the API? I can't find it here.
Search the [wiki](/../../wiki). It's still far from done, but it should help you! You can also open a Python interpreter and play around with the library. It's suited for experimentation and prototyping, to help prevent these exact cases.

If you still can't find it, I probably didn't implement it yet. This is still a work in progress. Don't worry though, I plan to have the entire public API mapped & available soon!

### I have a feature/change that I think should go in. How can I participate?
You can do one of two things:
 1. [Fork the repository](/../../fork) and make your changes. When you're done, send me a pull request and I'll look at it.
 2. [Open a ticket](/../../issues/new) and tell me about it. My aim is to create the best API library in terms of comfort, flexibility and capabilities, and I can't do that alone. I'd love to hear about your ideas.

### Is this official?
No, and it's also not endorsed in any way by Valve Corporation. _(obligatory legal notice)_ I couldn't find a fitting name at this point for it, so I just skipped it for now.

### Can I use this library in my busy web app?
No, not yet. :( I try to make sure I don't break anything when I make changes, but every now and then I might refactor it a bit. Right now, it's in a __shaky beta__ phase. (Why "shaky"? Because it's stable in terms of actual code, so "unstable" would be wrong.)

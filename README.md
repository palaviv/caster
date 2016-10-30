caster
======

Caster is a command line tool for casting media to chromecast.
Currently support python 2.7 and 3.5.

How to use
-----------

```
caster /file/to/play.mp4

caster /file/to/play.mp4 --device ChromcastName

caster /file/to/play.mp4 --subtitles /path/to/subtitles.vtt
```

### Player control

```
space -> toggle between play and pause.
up -> volume up.
down -> volume down.
right -> jump 30 seconds forward.
left -> jump 30 seconds backwards.
s -> stop.
```

Dependencies
------------

* pychromecast
* readchar

Install
-------

1. pip install caster


Development
-----------

This project is under development and any contribution is welcome.



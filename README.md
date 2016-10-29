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
space -> toggle between space and pause.
up -> volume up.
down -> volume down.
s -> stop.
```

Dependencies
------------

* pychromecast
* six
* readchar

Install
-------

1. Download the repository from https://github.com/palaviv/caster.
2. Run `python setup.py install`.


Development
-----------

This project is under development and any contribution is welcome.



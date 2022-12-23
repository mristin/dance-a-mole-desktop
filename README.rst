************
dance-a-mole
************

Dance the moles back into their holes instead of whacking them.

.. image:: https://github.com/mristin/dance-a-mole-desktop/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/mristin/dance-a-mole-desktop/actions/workflows/ci.yml
    :alt: Continuous integration

.. image:: https://media.githubusercontent.com/media/mristin/dance-a-mole-desktop/main/screenshot.png
    :alt: Screenshot

.. image:: https://media.githubusercontent.com/media/mristin/dance-a-mole-desktop/main/screenshot-game-over.png
    :alt: Screenshot Game Over

.. image:: https://media.githubusercontent.com/media/mristin/dance-a-mole-desktop/main/screenshot-youtube-standard.png
    :alt: Screenshot Youtube standard
    :target: https://www.youtube.com/shorts/KubgIO5jF-E

.. image:: https://media.githubusercontent.com/media/mristin/dance-a-mole-desktop/main/screenshot-youtube-plank.png
    :alt: Screenshot Youtube plank
    :target: https://www.youtube.com/watch?v=QVMEFmFwkKw

.. image:: https://media.githubusercontent.com/media/mristin/dance-a-mole-desktop/main/screenshot-youtube-jumping.png
    :alt: Screenshot Youtube jumping
    :target: https://www.youtube.com/shorts/zVW9MYvRWe0

Installation
============
Download and unzip a version of the game from the `Releases`_.

.. _Releases: https://github.com/mristin/dance-a-mole-desktop/releases

Running
=======
You need to connect the dance mat *before* starting the game.

Run ``dance-a-mole.exe`` (in the directory where you unzipped the game).

If you have multiple joysticks attached, the first joystick is automatically selected, and assumed to be the dance mat.

If the first joystick does not correspond to your dance mat, list the available joysticks with the following command in the command prompt:

.. code-block::

    dance-a-mole.exe --list_joysticks

You will see the names and unique IDs (GUIDs) of your joysticks.
Select the joystick that you wish by providing its GUI.
For example:

.. code-block::

    dance-a-mole.exe -joystick 03000000790000001100000000000000

Which dance mat to use?
=======================
We used an unbranded dance mat which you can order, say, from Amazon:
https://www.amazon.com/OSTENT-Non-Slip-Dancing-Dance-Compatible-PC/dp/B00FJ2KT8M

Please let us know by `creating an issue`_ if you tested the game with other mats!

.. _creating an issue: https://github.com/mristin/dance-a-mole-desktop/issues/new

Acknowledgments
===============
The mole sprites and the background were taken from: https://github.com/lepunk/react-native-videos/tree/whack-a-mole/WhackAMole/assets

The hour glass sprite has been taken from: https://olgas-lab.itch.io/hourglass

The sprites of vegetables have been taken from: https://opengameart.org/content/2d-vegetables

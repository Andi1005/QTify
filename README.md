# QTify
A web app where you can add songs to your Spotify queue.
Anybody with a code can access it, so you don't have to pass your phone around.

The name QTify is a mix of "Queue" and "Spotify" :)

# Outdated
At the time when I delveoped this app, there was no such feture in the normal Spotify. Now they have the same function with Spotify Yam.
Because of this the website is no longer avalible in the internet. Still, I am keeping the surce code here.

# How to access QTify
The website is hosted on [Pythonanywhere.com](https://eu.pythonanywhere.com) and can be accessed at [qtify.eu.pythonanywhere.com](http://qtify.eu.pythonanywhere.com/). 
On desktop the website may appear strange due to its focus on mobile browsers.

# Using QTify
On the index page you can choose to either create a new room or to join an existing one:

* If you **create** a new room, you are redirected to a page where you have to sing-in to Spotify.
After that you are again redirected to the host page. 
Here you can visit your newly created room yourself 
or you can sing-out and all your data will be deleted from the server.

* If you choose to **join** an existing room, you will be prompted to enter a pin.
You can get a pin from the host of the Room.

* There's also an option where you can scan a **QR Code** to enter a room directly.
The button to view the QR Code is at the top-left corner in the room page.


Finally, you are in the room page, the heart of the application. 
You can view the current playing song and its progress, 
search for songs to be added next and send them to the server by clicking on the song.

There is no way of deleting or changing tracks in the queue once the server sends them to Spotify :(



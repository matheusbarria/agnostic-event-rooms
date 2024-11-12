Matheus Barria and Patrick Schlosser

# Description
The goal of our project is to create semi-private application-agnostic event rooms that can be joined by a group for an online interaction. Our service will serve as a middleware that can relay requests and connect clients (users) and allow them to create a room but will not provide essential functionality but will rather relay requests to an application service. We will then build a small example chat service server to interconnect with our online room service to demonstrate functionality. The rooms should be able to host different events depending on the connection made such as jackbox style games, trivia, chat rooms, and other services that do not require a high rate of content delivery to clients.

# Application server 1: trivia-game
Install all of the dependencies:
`pip install -r requirements.txt`

and then to start the server, run:
`
uvicorn server:app --reload
`

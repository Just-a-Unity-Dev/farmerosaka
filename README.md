# farmerosaka

Basic discord bot for a private server.

## features

* Allow members to change the bot's profile picture
* Allow members to add statuses to the periodic status rotation
* Member custom role management through commands
* Admin-only SQL evaluation

## how do I host this

Clone the repo and set up venv with `python -m venv ./venv`

Ensure the packages are installed with `pip3 install -r requirements.txt`

You can run it straight out of the box or set up a systemd service like this:

```
[Unit]
Description=a landlord discord bot
After=network.target

[Service]
ExecStart=/PATH/TO/farmerosaka/venv/bin/python3 main.py
WorkingDirectory=/PATH/TO/farmerosaka/
StandardOutput=inherit
StandardError=inherit
Restart=always
User=BOT_RUNNER_USER_REPLACE_ME

[Install]
WantedBy=multi-user.target
```

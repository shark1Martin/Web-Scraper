# Web-Scraper

Let's make some dough.

Applications Required:

Library                             Purpose                                                     Install Command
-------                             -------                                                     ---------------
selenium                            Web Automation (browser control)                            pip install selenium

bs4 (BeautifulSoup)                 HTML parsing from page source                               pip install beautifulsoup4

requests                            Send push notifications requests to Pushover api            pip install requests

pymongo                             Interact with MongoDB Atlas                                 pip install pymongo

python-dotenv                       Load private security keys from .env file securely          pip install python-dotenv

lxml (optional but recommended)     Fastest parser for BeautifulSoup                            pip install lxml

flask                               Web framework                                               pip install flask

gunicorn                            WSGI server for deployment                                  pip install gunicorn

bcrypt                              Secure password hashing                                     pip install bcrypt

jinja2                              Templating engine used by Flask (comes with Flask)          (included with flask)

bson                                JSON-like format for MongoDB (via bson.json_util)           (included with pymongo)

werkzeug                            Used internally by Flask for routing and security	        (included with Flask)


Things to work on:

- Potentially make a Windows Tray App, for experience? (Slowly looking away at this..maybe ill do it for another project)

- <Add AI-based alert filters> ??? Recommended by ChatGPT, maybe ill learn some AI, lets do it!

- Make it work without having VSCODE/terminal always on.

- Add all entry categories (odds, amount, etc.)

- Fix the timezones for the graphs.

Update Log:

4/22/2025

It works in the background, but it needs the chrome profile to be already logged in and the browse always on.

Computer must also always be on, and I don't think its taking to much RAM (this can be debunked using IntelliJ, I know you can see the CPU?RAM usage there).

It scrapes, updates and sends notifications perfectly fine.

Only thing is that you need VSCODE/Terminal to be on.


4/24/2025

Finally added the .gitignore file so that I don't dox myself, my database and my notifications api...

Scraper now connects to MongoDB, where it cross-checks to see if there are any duplicates entries from the previous run, and saves new entries going forward.

Planning to visualize this data and make some detailed ai-analysis going forward.

Also planning to add a front-end dashboard and an application type installation if possible..


5/1/2025

Added some HTML for the front-end which includes a password page and a basic homepage with all the current entries.

Now I have to work on actually getting it to work online, not just on my local machine.

5/9/2025

Added roles such as admins and users. Added routes corresponding to each role.

Added a signup page for new users and admins that require a keycode to do so.

I'm trying to figure out how to use AI...hmm maybe something with analysis, or maybe some machine learning could be nice.

Also need to fix entries table, not enough information is being displayed, and the time is in UTC not EST, maybe I should add a configurable timezone feature.

5/10/2025

Add head admin role and its permissions to manage users and admins. Where admins can only manage users aswell.

Admin entry counter to visualize the how much data is coming in and the number of opportunities presented to the user every day and for the past week.

Added another graph in insights, but both graphs are in UTC, I need to fix that in the future.
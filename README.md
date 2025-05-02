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


Things to work on:

- Potentially make a Windows Tray App, for experience? (Slowly looking away at this..maybe ill do it for another project)

- <Add AI-based alert filters> ??? Recommended by ChatGPT, maybe ill learn some AI, lets do it!

- Make it work without having VSCODE/terminal always on.

- For the frontend, add the MongoDB Charts to the homepage and getting it online


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


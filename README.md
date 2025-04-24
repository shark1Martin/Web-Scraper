# Web-Scraper

Let's make some dough.

Applications Required:

- Pushover: To send notifications to your phone whenever the desired outcome appears.

- BeautifulSoup: To parse the web page and find the desired information to send to user.

- Selenium: To be able to open and operate on chrome. 

- Requests: To simplify the interaction with web services by abstracting complexities of manual HTTP connection management.


Things to work on:

- Make it so that it sends the entire bet entry (teams, odds, event, and bet amount)

- Potentially make a Windows Tray App, for experience?

- <Add AI-based alert filters> ??? Recommended by ChatGPT, maybe ill learn some AI, lets do it!

- Make it work without having VSCODE/terminal always on.

- Also fix the logging, the same %/$ can come up but be different you know...


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
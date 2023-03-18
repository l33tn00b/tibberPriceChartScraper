# tibberPriceChartScraper
Getting the Tibber Price Chart for Display on an ePaper Display

This is a breakout from [my efforts to get ready for Smart Grid integration](https://github.com/l33tn00b/GettingReadyForSmartGrid).

# Just why?
Dynamic pricing is an essential element of a future smart electrical grid because it allows for the efficient allocation of energy resources, encourages conservation during peak periods, and provides economic incentives for consumers to shift their energy usage to off-peak hours.

In a traditional electrical grid, the cost of electricity remains the same throughout the day, regardless of the level of demand. However, in a smart grid, energy prices can be adjusted based on real-time demand, supply, and other factors. This allows for more efficient use of energy resources, as prices can be adjusted to reflect the actual cost of generating and distributing electricity at different times of the day.

For example, during periods of high demand, such as hot summer afternoons when many people are using air conditioning, energy prices can be increased to encourage consumers to reduce their energy usage or shift it to off-peak hours when demand is lower. This reduces the strain on the grid and can help prevent blackouts or brownouts.

Dynamic pricing can also incentivize the use of renewable energy sources, such as solar and wind power. As these sources of energy are intermittent, dynamic pricing can encourage consumers to use energy when it is available and reduce usage when it is not. This can help to balance the grid and reduce the need for traditional fossil fuel power plants.

In addition, dynamic pricing can provide economic benefits for consumers. By offering lower prices during off-peak hours, consumers can save money on their energy bills by shifting their usage to those times. This can also help to reduce overall energy costs and improve energy affordability for consumers.

Overall, dynamic pricing is an essential element of a future smart electrical grid because it can help to improve grid efficiency, reduce the need for new infrastructure, promote renewable energy use, and provide economic benefits for consumers.

You might want an ePaper display for dynamic electricity pricing in your kitchen for several reasons:

1. Real-time information: By having a display for dynamic electricity pricing in their kitchen, you can have access to real-time information about the current cost of electricity. This can help you make informed decisions about when to use energy and when to conserve.

2. Energy conservation: Seeing the current price of electricity can encourage you to conserve energy during peak periods when prices are higher. For example, you may choose to delay running the dishwasher or washing machine until off-peak hours when electricity is cheaper.

3. Cost savings: By being aware of the current price of electricity, you can take advantage of off-peak pricing and shift your energy usage to those times when electricity is cheaper. This can result in lower energy bills and cost savings over time.

4. Environmental impact: By reducing your energy usage during peak periods, you can help to reduce the strain on the grid and promote a more sustainable energy system. This can help to reduce greenhouse gas emissions and support a cleaner energy future.

To sum up, having a display for dynamic electricity pricing in your kitchen can help you make more informed decisions about your energy usage and promote energy conservation, cost savings, and environmental sustainability.

# Which provider?
There's a limited number of providers offering dynamic electricity pricing in Germany. One of them is [_Tibber_](www.tibber.com). They offer pricing data via API for customers only. And I'm not a customer (yet). So we need to scrape the chart off their website and render it for the ePaper display. 

# How?
This will be based on https://www.stavros.io/posts/making-the-timeframe/.
The resulting picture for display (having completed steps given below):
![Image for ePaper Display](tibber_chart_inverted.png "Tibber Price Chart prepared for ePaper Display, Firefox Capture")

I've created a container automating the scraping and serving the image of the Tibber price chart for the Timeframe to fetch.
The container is based on [Selenium-Firefox](https://github.com/SeleniumHQ/docker-selenium) and has additional modifications to automate scraping and serving the result. The web server runs on port 8999 (https) using on-the-fly generated keys. 

Why that way? Because if your tool is a hammer, every problem looks like a nail. Tool = Selenium. 

# Alternatives 
Get raw pricing data from the European Transparency Platform, calculate pricing according to a particular provider. Render a nice chart ourselves. 

Benefits:
- Lightweight solution (smaller container). 
- Customizable chart. 

Drawbacks: 
- Requires detailed data on pricing components for each municipality. 
- Requires in-depth data on pricing calculation for each provider. 

# Customization 
The container is customized for my location. You will have / might want to change: 
- Zip code via ```ENV``` parameter in Dockerfile or at runtime (```-e "PLZ=<your zip code>"```). This will affect price calculation. Each municipality has different pricing.
- Zip Code check inside ```scripts/scrape_firefox.py```. Currently, only numbers are acceptable input.
- Timezone via ```ENV``` parameter (```-e "TZ=Europe/Berlin"```) at container startup.

# Issues
- Web Scraping the Chart needs a Browser (Selenium). So the server side component has to be run on a (relatively) beefy machine (so many dependencies). Can't additionally load my little Rapberry with this.
- (no:) Maybe using BeautifulSoup to extract the Tibber SVG chart and render it with something like Imagemagick? But there's the issue of having an interactive website (Zip Code...). So: no...

# Technical Deep-Dive
## Steps to scrape the chart using Selenium:
- Load cookies (cookie banner be gone) or run browser with appropriate extension (need to install it in Selenium container).
- Add Zip Code to input field: ```driver.find_element(By.XPATH, "/html/body/div[1]/main/div[4]/div/section/div/div[1]/div/div/div[1]/div/div/section/div[2]/div/div/div[1]/div/div/span/input")```
- Click Button: ```input_button = driver.find_element(By.XPATH,"/html/body/div[1]/main/div[4]/div/section/div/div[1]/div/div/div[1]/div/div/section/div[2]/div/div/div[1]/div/div/button")```
- Find chart: ```price_chart = driver.find_element(By.XPATH,"/html/body/div[1]/main/div[4]/div/section/div/div[1]/div/div/div[1]/div/div/section/div[2]/div")``` 
- Save Screenshot: ```price_chart.screenshot("<location>")```
This will -of course- be badly broken if Tibber decide to change their website (absolute XPATHs for identification of objects).

## Building a Container doing the scraping and conversion:
- Start by using the official Selenium Chrome Container (https://github.com/SeleniumHQ/docker-selenium): ```docker run selenium/standalone-chrome python3 --version``` Does it run? Good.
- Thank you, StackOverflow (https://stackoverflow.com/questions/47955548/docker-image-with-python3-chromedriver-chrome-selenium): Create a ```Dockerfile``` adding Selenium Python Modules to the already installed Selenium:
  ```
  FROM selenium/standalone-firefox
  USER root
  RUN wget https://bootstrap.pypa.io/get-pip.py
  RUN python3 get-pip.py
  RUN python3 -m pip install selenium
  ``` 

  Then build it: 
  ```
  docker build . -t selenium-firefox-test 
  ```
  There should be an image, now:
  ```
  root@dockerRunnerTest:/home/<username># docker image list
  REPOSITORY                   TAG       IMAGE ID       CREATED         SIZE
  selenium-firefox-test        latest    dbad8bee893c   2 hours ago     1.38GB
  selenium/standalone-firefox  latest    f8f3ec83b422   8 days ago      1.3GB
  hello-world                  latest    feb5d9fea6a5   17 months ago   13.3kB
  ```
  What an irony. Using a GB-sized container for generating a kB-sized image. 
  
  Run it, directly going to a Python shell:
  ```
  docker run -it --shm-size="2g" selenium-firefox-test python3
  ```
  Test it:
  ```
  >>> from selenium import webdriver
  >>> from selenium.webdriver.common.keys import Keys
  >>> from selenium.webdriver.common.by import By
  >>> driver=webdriver.Firefox()
  ...
  ```
  
  Run it detached:
  ```
  docker run -d -e "TZ=Europe/Berlin" -p 8999:8999 --name busy_shockley --shm-size="2g" selenium-firefox-test
  ```
  Need to have VNC ? Password is "secret".
  ```
  docker run -d -e "TZ=Europe/Berlin" -p 7900:7900 -p 8999:8999 --name busy_shockley --shm-size="2g" selenium-firefox-test 
  ```
  
  
  Connect to it:
  ```
  docker exec -it busy_shockley /bin/bash
  ```
  
  Need to download files? 
  Mount a host directory into the container. Need to fix permissions first (see https://github.com/SeleniumHQ/docker-selenium last section)
  ```
  cd /home/<username>/tibberPriceChartScraper
  mkdir download
  chown 1200:1201 download
  ```
  Start the container, mounting the newly created directory:
  ```
  docker run -d -e "TZ=Europe/Berlin" -p 7900:7900 -p 8999:8999 --shm-size="2g" --name busy_shockley -v /home/<username>/dockerSeleniumPython/download:/home/seluser/files selenium-firefox-test
  ```
 
## Scraping: 
Selenium's containers run Openshift. So there is a supervisord coordinating programs/services inside the container.
Selenium's supervisor configuration is given in ```/etc/supervisor/conf.d/selenium.conf```. We'll just add another ```.conf```file handling 
- Web Server Startup (nginx),
- Cron Startup,
- Initial scrape after container startup (further scrapes will be initiated by a cronjob starting the scrape script).
  
## Caveats
- Container Differences
  - Using Selenium-Chrome will drop you into a root shell in the container
  - Using Selenium-Firefox will drop you into a user shell in the container... 
That makes for quite a difference in behaviour. For the Firefox container, Python modules need to be installed as user seluser. 
In the Chrome container, you may install these as root. 
Do also make sure, you're running the scraping script from the user home directory or a directory that is at least user-writeable. Else the Selenium Driver for Firefox will fail miserably (complaining about missing write permission for a log file).

- Browser Differences  
  Screenshots will be different, see below. Firefox will give a better result by capturing the axes. So the script/Dockerfile is written for the Selenium-Firefox container.
  Chrome: 
  ![Chrome Screenshot](tibber_price_chart_chromium.png "Tibber Price Chart Render, Chromium Capture")
  Firefox: 
  ![Firefox Screenshot](tibber_price_chart_firefox.png "Tibber Price Chart Render, Firefox Capture")

- Cron:
  - cron needs to be (re-)started at container init (because there is no init system)
  - per-user crontabs are dicey. Use system-wide /etc/crontab instead.
  - Supervisor (I think) runs as non-root user in the Firefox container. So we cannot run conf-scripts demanding switching to user=root. Working around that by using sudo in the shell script.
  
- Encryption:
 Https keys generation: I'd have loved to properly do this on the fly at container startup. But generating keys takes quite a long time. So we either use shorter keys (or copy pre-made ones into the container).

- Time zone issues:
Getting the correct local time inside the Selenium container is quite a feat. Time zone is set via an env parameter. This will only be honored when in a normal shell (because the system in the cotainer still runs on UTC as set in /etc/timezone). When running our cronjob to do once-a-day scraping we'd like to add a timestamp to the image. But this is not a normal shell, it's a cronjob. So any time queries will fall back to responding in UTC. Resorted to exporting TZ Env Parameter before execution of the command. It works. Doesn't have to be beautiful.

# ToDo:
- Add conversion scripts from "The Timeframe" (rendering b/w image, still needs to be converted to binary)
- Modify Conversion Scripts to crop screenshot (done)
- Change background in selenium to white (for screenshot) (done, doesn't work, so we invert the colors using Python Imaging Library (Pillow))
- Change container time to local timezone (done, see https://github.com/SeleniumHQ/docker-selenium/wiki/Setting-a-Timezone)
- Add flask so we may serve the result directly from our container using Python (not, instead use proper server for https, nginx, done)
- Set Zip Code via env parameter at container startup (done)
- Add timestamp to screencapture to show latest update (done)
- Use generated/provided DH parameters (https://github.com/MarvAmBass/docker-nginx-ssl-secure/blob/master/ssl.conf)

# Things that probably never will come to pass:
- Proper certificates for https (maybe https://anuragbhatia.com/2020/05/sys-admin/automated-ssl-certificate-management-for-private-containers/)
- Give users a choice of length for DH group via env parameters (https://github.com/MarvAmBass/docker-nginx-ssl-secure).
- Proper handling of security updates (crude cron-based solution running unattended-upgrades once a day. Risk of breaking things.).
- Proper localization.

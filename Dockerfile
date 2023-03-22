# Use Firefox as a driver
# use latest
FROM selenium/standalone-firefox

# declare environment variable for zip code
# may be overridden by including -e "PLZ=<ZIP CODE>" in docker run command
ENV PLZ="20095"
# timezone may be set via env parameter 
# if not, we default to Europe, Germany
ENV TZ=Europe/Berlin

# add scraper script
USER seluser
ADD --chown=seluser:seluser scripts /home/seluser/scripts
RUN chmod a+x /home/seluser/scripts/run_scrape.sh 

# install python and useful tools
# as well as the conf file for 
# supervisord for initial scraping
# further scraping (once a day) will
# be initiated by a cron job calling the scraper
USER root
ADD conf_scripts /etc/supervisor/conf.d
ADD startup_scripts /opt/bin
# make sure scripts are executable
RUN chmod a+x /opt/bin/cronrestart.sh
RUN chmod a+x /opt/bin/gen-keys.sh
RUN chmod a+x /opt/bin/start-scraper.sh
# install python
RUN apt-get update && apt-get install python3-distutils -y
# now, this is contentious.
# the container will probably run for quite some time
# and i'll forget about it and only think of it when something breaks.
# so i'd rather break it by applying some update than having 
# security issues (other than weak ssh crypto and bad code :P ) 
RUN apt-get install unattended-upgrades -y
# cron for scraping once a day
RUN apt-get install cron -y
# add system-wide crontab for
# periodic scrape (seluser)
# unattended upgrades (root)
ADD crontab/crontab /etc/crontab
# we'll restart later, but why not
RUN service cron start
RUN apt-get install nano -y
# add nanorc file with tabstospaces and 4 spaces
ADD --chown=seluser:seluser nano_cust/.nanorc /home/seluser
ADD nano_cust/.nanorc /root
# navigate 
RUN apt-get install mc -y
# install https server
RUN apt-get install nginx -y
# add config
ADD nginx_config/default-ssl /var/tmp
# load dafault_image (no data yet)
ADD default_image /var/www
# expose https port for timeframe to fetch rendered picture
EXPOSE 8999
# prepare python for package installation
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py

# switch back so seluser, python
# libraries are to be installed per-user 
# this is different in the chromium-based
# selenium container
USER seluser
RUN python3 -m pip install selenium
RUN python3 -m pip install Pillow
RUN python3 -m pip install numpy
RUN python3 -m pip install pyyaml



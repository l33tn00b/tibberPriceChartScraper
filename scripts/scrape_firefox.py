# intended to be a short script
# aber wir haben schon wieder ein Waffensystem draus gemacht...

# timestamps
import datetime

# hash calculation
# for image update check
import hashlib

#image color manipulation
import numpy as np

# serialize cookies
# doesn't work consistently...
import pickle

# render / modify images
from PIL import Image, ImageEnhance, ImageDraw
import PIL.ImageOps

# env
import os

# selenium for scraping
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.color import Color

# launching subprocesses (shell commands)
import subprocess

# exit
import sys

# wait for website to render chart
# and timestamping
import time
from time import strftime

# get config from file
import yaml

def create_error_image(errmsg: str):
    """
    Create an image for display on a Lilygo T5 4.7" ePaper.
    The image contains a short text (parameter errmsg) giving the
    reason for the error.
    Returns a b/w PIL image which has to be saved and/or encoded for
    display using bincode_image().
    By-product is a png file written to local directory so as to have a
    human-readable description.
    """
    # create new white background image
    img = Image.new('1', (960, 540), color = 'white')
    # print current (local) time on it
    now = datetime.datetime.now()    
    ImageDraw.Draw(img).text((2, 80),now.strftime('%Y-%m-%d %H:%M:%S'),(0))
    # print error message on it
    ImageDraw.Draw(img).text((2, 90),errmsg,(0))
    # write it in png format so we may easily read it
    # from a normal web browser
    outfile_name = config_file.get("outfile_name")
    img.save(outfile_name+".png")
    if config_file.get("copy_to_www_dir") == True:
        copy_to_wwwdir(outfile_name+".png")
    return img
    
def bincode_image(im: Image, outfile:str):
    """
    Takes a PIL Image (im) to be encoded for display
    on the ePaper and to be written to a file named
    outfile.
    Writes hash file to disk using calc_bin_image_hash().
    Doesn't return any value.
    """
    contents = []
    # Write output file.
    for y in range(0, im.size[1]):
        value = 0
        done = True
        for x in range(0, im.size[0]):
            pixel = im.getpixel((x, y))
            if x % 2 == 0:
                value = pixel >> 4
                done = False
            else:
                value |= pixel & 0xF0
                contents.append(value.to_bytes(1, "little"))
                done = True
        if not done:
            contents.append(value.to_bytes(1, "little"))
    data = b"".join(contents)
    print(type(data))
    with open(outfile, "wb") as f:
        f.write(data)
    #content_hash = hashlib.sha256(data).hexdigest()
    #with open(outfile + ".sha", "wb") as f:
    #    f.write(content_hash.encode())
    calc_bin_image_hash(data, outfile)
    if config_file.get("copy_to_www_dir") == True:
        copy_to_wwwdir(outfile)

def prep_image(infilename: str):
    """
    Prepare image given in file for conversion to ePaper binary format.
    Returns b/w PIL image object
    """
    # open previously saved image
    im = Image.open(infilename)
    # take relevant part (chart and text above)
    im = im.crop((0,0,im.width, 800))
    # https://stackoverflow.com/questions/3752476/python-pil-replace-a-single-rgba-color
    # image is rgba
    r,g,b,a = im.split()
    # drop the a
    rgb_image = Image.merge('RGB', (r,g,b))
    # invert it
    inverted_image = PIL.ImageOps.invert(rgb_image) #im = im.convert('RGBA')
    im = inverted_image.convert('RGBA')
    data = np.array(im)   # "data" is a height x width x 4 numpy array
    red, green, blue, alpha = data.T # Temporarily unpack the bands for readability
    # Replace the previously (now inverted)
    # black background with white... (leaves alpha values alone...)
    black_areas = (red == 235)  & (green == 227) & (blue == 219)
    data[..., :-1][black_areas.T] = (255, 255, 255)
    # tooltip background is too dark. brighten a bit for dithering
    tooltip_area = (red == 224)  & (green == 214) & (blue == 204)
    #data[..., :-1][tooltip_area.T] = (246, 240, 225)
    data[..., :-1][tooltip_area.T] = (255, 255, 255)
    # replace some pixels of pricing text (max price)
    highprice_text = (red == 116)  & (green == 214) & (blue == 185)
    data[..., :-1][highprice_text.T] = (0,0,0)
    highprice_text = (red == 176)  & (green == 220) & (blue == 202)
    data[..., :-1][highprice_text.T] = (0,0,0)
    # Transpose back
    im2 = Image.fromarray(data)
    inverted_im_not_resampled = im2
    #im2.show()

    # resize (i.e. downsize) image
    # size set for lilygo t5 4.7 inch
    size = 960, 540
    im2.thumbnail(size, Image.Resampling.LANCZOS)
    
    now = datetime.datetime.now()    
    ImageDraw.Draw(im2).text((0, 80),now.strftime('%Y-%m-%d %H:%M:%S'),(0, 0, 0))
    # debug: write intermediate product to disk
    outfile_name = config_file.get("outfile_name")
    im2.save(outfile_name+'_chart_inverted.png')

    inverted_resampled = inverted_im_not_resampled
    inverted_resampled.thumbnail(size, Image.Resampling.LANCZOS)
    # if > thresh pixel will be set wo white
    # else black
    thresh = 220
    fn = lambda x : 255 if x > thresh else 0
    bw_image_inv_res = inverted_resampled.convert('L').point(fn, mode='1')
    bw_image_inv_res.save(outfile_name+'_chart_inv_res_bw.png')

    bw_image_inv_res.save('image.png')
    if config_file.get("copy_to_www_dir") == True:
        copy_to_wwwdir('image.png')
    
    # change to black and white image
    # with custom threshold
    # instead of dithering
    # https://stackoverflow.com/questions/9506841/using-pil-to-turn-a-rgb-image-into-a-pure-black-and-white-image
    #thresh = 200
    #fn = lambda x : 255 if x > thresh else 0
    #bw_image = inverted_image.convert('L').point(fn, mode='1')

    #size = 960, 540
    #bw_image.thumbnail(size, Image.Resampling.LANCZOS)
    #ImageDraw.Draw(bw_image).text((2, 80),now.strftime('%Y-%m-%d %H:%M:%S'),(0))
    #bw_image = inverted_im_not_resampled.convert('L').point(fn, mode='1')
    # debug: write intermediate product to disk
    #bw_image.save(outfile_name+'_chart_bw.png')
    # dithered image
    # doesn't give a good result
    # especially wrt background and tool tip indicating current price
    #bw_dithered_image = im2.convert('1')
    #bw_dithered_image.save('d:\\downloads\\tibber_chart_bw_dithered.png')
    return bw_image_inv_res

def calc_bin_image_hash(data: bytes, bin_filename: str):
    """
    Calculate SHA-256 hash of data
    Write to file given by binFileName appending .sha to it
    Returns hash. If specified, copy hash file to www dir.
    """
    content_hash = hashlib.sha256(data).hexdigest()
    with open(bin_filename + ".sha", "wb") as f:
        f.write(content_hash.encode())
    if config_file.get("copy_to_www_dir") == True:
        copy_to_www_dir(bin_filename + ".sha")
    return content_hash


def copy_to_wwwdir(infilename: str):
    """
    Copy file to www server directory.
    Destination path must be given in config file (www_dir).
    infilename will be appended to path given in config file.

    Be careful. Destination files will be overwritten!
    Must be able to sudo (which is to be provided to the user
    running this script by the container environment).
    """
    # copy to web server directory
    # yessir to any prompt
    # you have been warned!
    # ToDo: Change container environment to be able to do this
    # without sudo (big change). Usage of sudo makes this a script reliant
    # on a unix-like environment.
    www_dir = config_file.get("www_dir")
    # this is so unsafe...
    # please, please, never mount any host dir into the container
    cmd_str = "yes | sudo cp " + infilename + " " + www_dir+"/"+infilename
    print(cmd_str)
    subprocess.run(cmd_str, shell=True)

if __name__ == '__main__':
    # read config from file
    try:
        config_file = yaml.safe_load(open("config.yaml",'rb'))
    except:
        print("Unable to load config file. Either non-existent or corrupt.")
        sys.exit(1)

    #start scraping
    driver = webdriver.Firefox()
    # firefox: we need to get the URL before loading cookies...
    url = config_file.get("website_URL")
    driver.get(url)
    # frage: wie handeln wir cookies?
    # antwort: wir speichern sie einmal (wenn wir alle akzeptiert haben)
    # untenstehende zeile brauchen wir also nur einmal, dann nicht mehr
    # pickle.dump(driver.get_cookies(), open("tibber_cookies.pkl", "wb"))
    # und dann laden wir sie einfach wieder
    cookie_filename = config_file.get("cookie_file")
    cookies = pickle.load(open(cookie_filename, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    # seite  muss nach dem laden der cookies neu geladen werden
    # expected behaviour. wtf.
    # bei chrome gehts auch ohne...
    driver.get(url)
    try:
        zip_input_xpath = config_file.get("zip_code_input_xpath")
        get_zip_code_from_env = config_file.get("zip_code_from_env")
        plz_feld = driver.find_element(By.XPATH, zip_input_xpath)
        if get_zip_code_from_env == False:
            try:
                zip_code = config_file.get("zip_code")
            except:
                # set to none for error image generation
                zip_code = None
        else:
            # get zip code from environment
            if "PLZ" in os.environ:
                zip_code = os.environ.get('PLZ')
            else:
                zip_code = None
        if not zip_code:
            create_error_image("Failed getting Zip Code. Neither Env nor config file.")
            outfile_name = config_file.get("outfile_name")
            bincode_image(error_image, outfile_name+".bin")
            sys.exit(1)
        # if all went well: send zip code to input field
        plz_feld.send_keys(zip_code)
    except:
        # if entering failed (but we had a zip code from config
        # or env
        print("Failed entering Zip Code. Exiting.")
        driver.close()
        # write and copy image having error message
        error_image = create_error_image("Failed entering Zip Code.\n Website has changed?")
        outfile_name = config_file.get("outfile_name")
        bincode_image(error_image, outfile_name+".bin")
        sys.exit(1)
        
    try:
        input_button_xpath = config_file.get("input_button_xpath")
        input_button = driver.find_element(By.XPATH,input_button_xpath)
    except:
        print("Failed finding price check button. Exiting.")
        driver.close()
        # write and copy image having error message
        error_image = create_error_image("Failed finding price check button.\n Website has changed?")
        outfile_name = config_file.get("outfile_name")
        bincode_image(error_image, outfile_name+".bin")
        sys.exit(1)     

    #sometimes, cookies will not be re-accepted.
    try:
        # we'd not be able to click the submit button
        # because it is obscured by the cookie banner
        # fck 
        input_button.click()
    except:
        try:
            print("Failed clicking price check button. Probably because cookies not re-accepted. Will try to click banner...")
            # find "accept all" button
            accept_button_xpath = config_file.get("cookie_accept_button_xpath")
            accept_button = driver.find_element(By.XPATH,accept_button_xpath)
            accept_button.click()
            #re-try clicking submit
            input_button.click()
        except:
            print("Failed clicking cookie banner. Exit.")
            driver.close()
            # write and copy image having error message
            error_image = create_error_image("Failed clicking cookie banner.\n Website has changed?")
            outfile_name = config_file.get("outfile_name")
            bincode_image(error_image, outfile_name+".bin")
            sys.exit(1)             
    
    # wir müssen allerdings warten, bis wir das ding gefunden haben...
    # weil das ja dynamisch gemacht wird sind wir auf einem
    # schnellen rechner manchmal zu schnell und screenshotten, bevor
    # das diagramm aufgebaut ist. wtf
    # mit zeitleiste untendran und y-achse:
    time.sleep(2)    

    try:
        price_chart_xpath = config_file.get("price_chart_xpath")
        price_chart = driver.find_element(By.XPATH,price_chart_xpath)
    except:
        print("Failed finding price chart. Exiting.")
        driver.close()
        # write and copy image having error message
        create_error_image("Failed finding price chart.\n Website has changed?")
        outfile_name = config_file.get("outfile_name")
        bincode_image(error_image, outfile_name+".bin")
        sys.exit(1)
        
    # so we'll just invert the resulting image
    # and use pil to pre-process it. Dooh...
    # see prep_image function
    outfile_name = config_file.get("outfile_name")
    price_chart.screenshot(outfile_name+'.png')    
    driver.close()
    chart_image = prep_image(outfile_name+'.png')
    #bincode_image includes hash calculation.
    bincode_image(chart_image, outfile_name + ".bin")


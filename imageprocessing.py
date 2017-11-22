
import os
from os.path import join, isdir
import sys

from colorthief import ColorThief
from PIL import Image, ImageDraw
from io import BytesIO


import requests
import asyncio

import time
import logging


@asyncio.coroutine
def getTop3colors(writefile, logger = None, PathDict = None, saveRawImg = False, saveColorPalette = False, resize = True):
    
    '''Get top 3 dominant colors from an url. 
    Algorithm credits to https://github.com/fengsp/color-thief-py

    Parameters
    ----------
    writefile: string, file path to result file
    logger: logging object from python's loggoing module, logging the program processes
    PathDict: dictionary, stores paths for saving raw image/color palette
    saveRawImg: boolean, true for saving the raw image downloaded from the url
    saveColorPalette: boolean, true for saving the top 3 dominant color palette
    resize: boolean, true for resizing raw image to 150x150 

    Returns
    -------
    None
    '''

    width, height = 150, 150 
    i = 0
    start = time.time()

    while True:

        url = yield #receive url

        #################Download / Read Image from web use requests###############
        response = requests.get(url)
        if response.status_code == 200:
            IMG = ColorThief(BytesIO(response.content))
            if saveRawImg:
                try:
                    with open(PathDict[url][0], 'wb') as file:
                        file.write(response.content)
                except Exception as e:
                    raise e
            if resize:
                IMG.image = IMG.image.resize((width, height), Image.NEAREST)
                

        #################Get color palette##################
            
            topcolors = IMG.get_palette(color_count=3,quality=10)[:3]
            if saveColorPalette:
                try:
                    palette = Image.new('RGB', (20*3, 20))
                    draw = ImageDraw.Draw(palette)
                    x = 0
                    for col in topcolors:
                        draw.rectangle([x, 0, x+20, 20], fill=col)
                        x += 20
                    del draw
                    palette.save(PathDict[url][1], "PNG")
                except Exception as e:
                    raise e

        ####################write result to file####################
            try:
                #colors = topcolors
                color_rgb = [','.join(map(str, col)) for col in topcolors]
                res = "{};{}".format(url, ";".join(color_rgb))
                writefile.write(res+"\n")
            except Exception as e:
                raise e

        ########Write cost of time processing 100 images to logger###########
        #################Took about 39 seconds on average####################
            if logger:
                i += 1
                if i%100==0:       
                    logger.info('processed 100 images, took %.0f seconds' % (time.time()-start))
                    start = time.time()
                    i = 0

        else:
            print("Missed image: %s"%url)



def main(urlfilepath='urls.txt', writefilepath='result.csv', saveImg = False):
    
    '''Read image urls from a text file, 
    get the top 3 dominant colors in RGB scheme, 
    write the result to a CSV file.

    Parameters
    ----------
    urlfilepath: string, input filename 
    writefilepath: string, output filename
    saveImg: boolean, true for saving downloaded raw images and generated color palette
    
    Return
    ------
    None
    '''
    
    img_path = 'imgs/'

    if len(sys.argv)>=2 and sys.argv[1]=='save':
        saveImg=True

    if saveImg and not isdir(img_path):
        os.mkdir(img_path)
        
    PathDict = {}

    logging.basicConfig(filename="%s.log"%sys.argv[0], level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        
        writefile = open(writefilepath, 'w')
        urlfile = open(urlfilepath,'r')
        
        if saveImg:        
            helper = getTop3colors(writefile=writefile, logger=logger, PathDict = PathDict, saveRawImg=True, saveColorPalette=True)
        else:
            helper = getTop3colors(writefile=writefile, logger=logger)
        next(helper)
        
        i = 0
        for url in urlfile:
            url = url.strip('\n')
            if saveImg:
                i += 1
                PathDict[url] = [join(img_path, "%d_raw.png"%i), join(img_path, "%d_colors.png"%i)]

            helper.send(url)
        
            

    except Exception as e:
        raise e
    finally:
        writefile.close()
        urlfile.close()



                    
if __name__ == '__main__':
    main(saveImg=False)





	
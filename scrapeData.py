#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import bisect


def customaxis(ax, c_left='k', c_bottom='k', c_right='none', c_top='none', lw=2, size=12, pad=8):
    '''
    From stackoverflow. User gcalmettes
    '''
    for c_spine, spine in zip([c_left, c_bottom, c_right, c_top],
                              ['left', 'bottom', 'right', 'top']):
        if c_spine != 'none':
            ax.spines[spine].set_color(c_spine)
            ax.spines[spine].set_linewidth(lw)
        else:
            ax.spines[spine].set_color('none')
    if (c_bottom == 'none') & (c_top == 'none'): # no bottom and no top
        ax.xaxis.set_ticks_position('none')
    elif (c_bottom != 'none') & (c_top != 'none'): # bottom and top
        ax.tick_params(axis='x', direction='out', width=lw, length=7,
                      color=c_bottom, labelsize=size, pad=pad)
    elif (c_bottom != 'none') & (c_top == 'none'): # bottom but not top
        ax.xaxis.set_ticks_position('bottom')
        ax.tick_params(axis='x', direction='out', width=lw, length=7,
                       color=c_bottom, labelsize=size, pad=pad)
    elif (c_bottom == 'none') & (c_top != 'none'): # no bottom but top
        ax.xaxis.set_ticks_position('top')
        ax.tick_params(axis='x', direction='out', width=lw, length=7,
                       color=c_top, labelsize=size, pad=pad)
    if (c_left == 'none') & (c_right == 'none'): # no left and no right
        ax.yaxis.set_ticks_position('none')
    elif (c_left != 'none') & (c_right != 'none'): # left and right
        ax.tick_params(axis='y', direction='out', width=lw, length=7,
                       color=c_left, labelsize=size, pad=pad)
    elif (c_left != 'none') & (c_right == 'none'): # left but not right
        ax.yaxis.set_ticks_position('left')
        ax.tick_params(axis='y', direction='out', width=lw, length=7,
                       color=c_left, labelsize=size, pad=pad)
    elif (c_left == 'none') & (c_right != 'none'): # no left but right
        ax.yaxis.set_ticks_position('right')
        ax.tick_params(axis='y', direction='out', width=lw, length=7,
                       color=c_right, labelsize=size, pad=pad)

def scrapeLinksElpais(urlPartido,linkPartido,rang0,rangF):
    import urllib3
    from bs4 import BeautifulSoup # third-party library!
    import urllib.parse as urlparse
    http = urllib3.PoolManager()
    list_urls = []

    for i in range(rang0,rangF):
        print(i)
        url = urlPartido+str(i)
        r = http.urlopen('GET', url, preload_content=False)
        html = r.read()
        soup = BeautifulSoup(html)
        list_links = soup.find_all('a')


        for tag in list_links:
            link = tag.get('href', None)
            if link != None:
                linkComplete = urlparse.urljoin(url,link)
                #print(linkComplete)
                if ("html" in linkComplete) and ("elpais.com/politica" in linkComplete) and ("actualidad" in linkComplete):
                    list_urls.append(linkComplete)


    list_urls = list(set(list_urls))
    #print(list_urls)
    with open(linkPartido, "w") as f:
        for u in list_urls:
            f.write(u+"\n")

def scrapeTextElpais(partido, linkPartido):
    import re
    import urllib3
    import string
    from bs4 import BeautifulSoup # third-party library!
    pattern = re.compile("<[^\<\>]*>")


    stop = ["podemos","pp","psoe","ciudadanos","ganemos","ahora"]
    with open('./data/spanish_stop.txt') as f:
        for line in f:
            stop.append(line.strip())
    patternStop = re.compile(r'\b(' + r'|'.join(stop) + r')\b\s*')
    http = urllib3.PoolManager()
    with open(linkPartido) as f:
        i = 0
        for url in f:
            print(i)
            if i > 5000: break #Enough news, randomly distributed
            i += 1
            if i < 1340: pass
            else:
                r = http.urlopen('GET', url.rstrip(), preload_content=False)
                html = r.read()
                soup = BeautifulSoup(html)
                text  = soup.find("div", {"id": "cuerpo_noticia"})
                try: iz = str(text.find("div", {"class": "izquierda"}))
                except: iz = ""
                try: de = str(text.find("div", {"class": "derecha"}))
                except: de = ""
                text = str(text)
                text = text.replace(iz,"").replace(de,"")
                text = text.translate(string.maketrans("",""), string.punctuation+'“”')
                #text = patternStop.sub('', text)

                text = re.sub(pattern,"",text).rstrip().lstrip()

                text = ' '.join([word for word in text.split() if word not in stop])

                ind = url.find("/20")

                date = url[ind+1:ind+11].replace("/","_")
                with open(partido+date+str(i)+".txt","w") as outfile:
                    outfile.write(text)
                #print(url)
                #print(text)

def happiness(partido,path,periodico,lang = 'spanish'):
    from labMTsimple import storyLab
    from os import listdir
    import datetime as dt
    import time
    import string

    labMT,labMTvector,labMTwordList = storyLab.emotionFileReader(stopval = 0.0,fileName='labMT2'+lang+'.txt',returnVector=True)

    stop = []

    count = 0
    files = listdir(path)
    files = [_ for _ in files if ((not "link" in _) and (not "dat" in _) and (partido in _))]
    files.sort()

    dates = []
    meanHap = []
    i = 0
    for file in files:
        i += 1
        if i%10 == 0: print(100.*i/len(files))
        with open(path+file) as f:
            print(file)
            dates.append(dt.datetime.strptime(file[file.find("_20")+1:file.find("_20")+11],"%Y_%m_%d"))

            noticia = f.read()
            noticia = noticia.translate(string.maketrans("",""), string.punctuation+'“”')
            count += 1
            saturdayValence,saturdayFvec = storyLab.emotion(noticia,labMT,shift=True,happsList=labMTvector)
            saturdayFvec = np.asarray(saturdayFvec)

            saturdayStoppedVec = storyLab.stopper(saturdayFvec,labMTvector,labMTwordList,stopVal=1.0,ignore=stop)
            saturdayValence = storyLab.emotionV(saturdayStoppedVec,labMTvector)

            meanHap.append(saturdayValence)

    dates = np.asarray([time.mktime(_.timetuple()) for _ in dates])
    np.savetxt(periodico+partido+"_dates.dat",dates)
    np.savetxt(periodico+partido+"_happ.dat",meanHap)


def plotHapp(periodico,year="2014"):
    import statsmodels.api as sm
    import pylab as plt
    import time
    import datetime as dt

    from matplotlib import rc
    rc('text', usetex=False)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for partido in ["pp","psoe","podemos","cs"]:
        x = np.loadtxt(periodico+partido+"_dates.dat")
        y = np.loadtxt(periodico+partido+"_happ.dat")

        if partido =="podemos" or partido == "cs":
            year = "2014"
        else:
            year = "2000"
        y = y[x>time.mktime(dt.datetime.strptime(year+"_02_15","%Y_%m_%d").timetuple())]
        x = x[x>time.mktime(dt.datetime.strptime(year+"_02_15","%Y_%m_%d").timetuple())]

        x = x[y>0]
        y = y[y>0]
        lowess = sm.nonparametric.lowess(y, x, frac=0.4)

        x1 = [dt.datetime.strptime(time.strftime('%Y-%m-%d', time.localtime(_-1000000)),'%Y-%m-%d') for _ in x]

        x2 = [dt.datetime.strptime(time.strftime('%Y-%m-%d', time.localtime(_-1000000)),'%Y-%m-%d') for _ in lowess[:, 0]]

        #ax.plot(x1, y, 'o',markerfacecolor=(255./255,187./255,120./255),markeredgecolor="none")
        ax.plot(x2, lowess[:, 1],linewidth=3,label=partido,alpha=0.7)
    ax.set_ylabel("Positividad de la noticia")
    ax.set_xlabel("Tiempo")
    plt.legend()
    ax.set_title("Positividad en las noticias de "+periodico)
    ax.set_ylim((6.,6.5))
    customaxis(ax)

    plt.savefig(periodico+"all.pdf")
    plt.savefig(periodico+"all.jpg")
    plt.show()

#urlPartido,linkPartido,rang0,rangF = "http://elpais.com/tag/podemos/a/", "./elpais/elpais_podemos_links.txt", 1, 55
#urlPartido,linkPartido,rang0,rangF = "http://elpais.com/tag/cs_ciudadanos_partido_de_la_ciudadania/a/",  "./elpais/elpais_cs_links.txt", 1, 26
#urlPartido,linkPartido,rang0,rangF = "http://elpais.com/tag/pp_partido_popular/a/",  "./elpais/elpais_pp_links.txt",1, 4138
#urlPartido,linkPartido,rang0,rangF = "http://elpais.com/tag/psoe_partido_socialista_obrero_espanol/a/",  "./elpais/elpais_psoe_links.txt",1, 5235
#scrapeLinksElpais(urlPartido,linkPartido,rang0,rangF)

#partido, linkPartido = "./elpais/elpais_podemos_", "./elpais/elpais_podemos_links.txt"
#partido, linkPartido = "./elpais/elpais_cs_", "./elpais/elpais_cs_links.txt"
#partido, linkPartido = "./elpais/elpais_pp_", "./elpais/elpais_pp_links.txt"
#partido, linkPartido = "./elpais/elpais_psoe_", "./elpais/elpais_psoe_links.txt"
#scrapeTextElpais(partido, linkPartido)

#happiness("podemos","./elpais/","elpais_")
#happiness("pp","./elpais/","elpais_")
#happiness("psoe","./elpais/","elpais_")
#happiness("cs","./elpais/","elpais_")
#plotHapp("elpais_")


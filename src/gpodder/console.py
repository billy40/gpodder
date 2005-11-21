#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

from libgpodder import gPodderChannelReader
from libgpodder import gPodderChannelWriter
from libgpodder import gPodderLib
from libpodcasts import podcastChannel
from librssreader import rssReader
from libwget import downloadThread


#TODO: move to libwget??
class DownloadPool:
    def __init__(self, max_downloads = 3):
        assert(max_downloads > 0)
        
        self.max_downloads = max_downloads
        self.cur_downloads = 0

    def addone(self):
        self.cur_downloads += 1

    def set(self):
        '''Ping function for downloadThread'''
        if self.cur_downloads >0:
            self.cur_downloads -= 1
        else:
            self.cur_downloads = 0
    
    def may_download(self):
        return self.cur_downloads < self.max_downloads


def list_channels():
    reader = gPodderChannelReader()
    reader.read()
    for id, channel in enumerate(reader.channels):
        print "%s: %s" %(id, channel.url)

def add_channel(url):
    reader = gPodderChannelReader()
    channels = reader.read()

    cachefile = gPodderLib().downloadRss(url)
    rssreader = rssReader()
    rssreader.parseXML(url, cachefile)
        
    channels.append(rssreader.channel)
    gPodderChannelWriter().write(channels)

def del_channel(chid):
    #TODO maybe add id to channels.xml 
    reader = gPodderChannelReader()
    channels = reader.read()
    if chid >=0 and chid < len(channels):
        ch = channels.pop(chid)
        print 'delete channel: %s' %ch.url
        gPodderChannelWriter().write(channels)
    else:
        print '%s is not a valid id' %str(chid)


def update():
    reader = gPodderChannelReader()
    reader.read(True)


def run():
    '''Update channels und download all items which are not already downloaded'''
    reader = gPodderChannelReader()
    updated_channels = reader.read(True)

    pool = DownloadPool()
    
    for channel in updated_channels:
       for item in channel.items:
           filename = gPodderLib().getPodcastFilename(channel, item.url)
           #TODO: do not check here with os.path. This should be part of item/gPodderLib ala item.already_downloaded()
           if not os.path.exists(filename):
               while not pool.may_download():
                   time.sleep(3)
               
               pool.addone()
               #thread will call pool.set() when finished
               thread = downloadThread(item.url, filename, pool)
               thread.download()
               
    
